from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import Listing, Booking, payment
from .serializers import ListingSerializer, BookingSerializer, PaymentInitiationSerializer, PaymentVerificationSerializer, PaymentSerializer
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
import uuid
from .services.payment_service import ChapaPaymentService
from .tasks import send_payment_confirmation_email

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    
    @action(detail=True, methods=['get'])
    def bookings(self, request, pk=None):
        """
        Retrieve all bookings for a specific listing
        """
        listing = self.get_object()
        bookings = Booking.objects.filter(listing=listing)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

class BookingViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing bookings.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new booking with validation
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Add any custom validation logic here
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    """
    Initiate payment for a booking
    """
    serializer = PaymentInitiationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    booking_id = serializer.validated_data['booking_id']
    return_url = serializer.validated_data.get('return_url', settings.DEFAULT_RETURN_URL)
    
    try:
        # Get booking
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        
        # Check if payment already exists
        if hasattr(booking, 'payment'):
            return Response(
                {'error': 'Payment already initiated for this booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create payment record
        transaction_id = f"ALX-TRAVEL-{uuid.uuid4().hex[:16]}"
        payment = Payment.objects.create(
            booking=booking,
            transaction_id=transaction_id,
            amount=booking.total_price,
            currency='ETB'
        )
        
        # Initiate payment with Chapa
        chapa_service = ChapaPaymentService()
        payment_result = chapa_service.initiate_payment(
            amount=float(booking.total_price),
            email=request.user.email,
            first_name=request.user.first_name or 'Customer',
            last_name=request.user.last_name or 'User',
            transaction_id=transaction_id,
            return_url=return_url
        )
        
        if payment_result['success']:
            # Update payment with payment URL
            payment.payment_url = payment_result['payment_url']
            payment.save()
            
            payment_serializer = PaymentSerializer(payment)
            return Response({
                'message': 'Payment initiated successfully',
                'payment_url': payment_result['payment_url'],
                'transaction_id': transaction_id,
                'payment': payment_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            # Mark payment as failed
            payment.mark_as_failed()
            return Response(
                {'error': payment_result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Booking.DoesNotExist:
        return Response(
            {'error': 'Booking not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    """
    Verify payment status
    """
    serializer = PaymentVerificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    transaction_id = serializer.validated_data['transaction_id']
    
    try:
        payment = get_object_or_404(
            Payment, 
            transaction_id=transaction_id,
            booking__user=request.user
        )
        
        # Verify payment with Chapa
        chapa_service = ChapaPaymentService()
        verification_result = chapa_service.verify_payment(transaction_id)
        
        if verification_result['success']:
            if verification_result['status'] == 'success':
                # Payment successful
                payment.mark_as_success(verification_result['chapa_transaction_id'])
                
                # Send confirmation email asynchronously
                send_payment_confirmation_email.delay(
                    request.user.email,
                    payment.booking.booking_reference,
                    str(payment.amount)
                )
                
                payment_serializer = PaymentSerializer(payment)
                return Response({
                    'message': 'Payment verified successfully',
                    'status': 'success',
                    'payment': payment_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                # Payment failed or pending
                payment.status = verification_result['status']
                payment.save()
                
                payment_serializer = PaymentSerializer(payment)
                return Response({
                    'message': f'Payment status: {verification_result["status"]}',
                    'status': verification_result['status'],
                    'payment': payment_serializer.data
                }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': verification_result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Payment.DoesNotExist:
        return Response(
            {'error': 'Payment not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status(request, transaction_id):
    """
    Get payment status
    """
    try:
        payment = get_object_or_404(
            Payment, 
            transaction_id=transaction_id,
            booking__user=request.user
        )
        
        payment_serializer = PaymentSerializer(payment)
        return Response({
            'payment': payment_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Payment.DoesNotExist:
        return Response(
            {'error': 'Payment not found'},
            status=status.HTTP_404_NOT_FOUND
        )