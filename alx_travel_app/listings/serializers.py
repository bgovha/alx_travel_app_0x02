from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Listing, Booking, Review, Payment

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class ReviewSerializer(serializers.ModelSerializer):
    guest = UserSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'guest', 'rating', 'comment', 'created_at']

class ListingSerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'address', 'city', 'country',
            'price_per_night', 'max_guests', 'bedrooms', 'bathrooms',
            'property_type', 'amenities', 'is_available', 'host', 'reviews',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['host', 'created_at', 'updated_at']

class BookingSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)
    guest = UserSerializer(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'listing', 'guest', 'check_in', 'check_out',
            'total_price', 'guests_count', 'status', 'special_requests',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['guest', 'total_price', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Validate booking dates and guest count
        """
        if data['check_in'] >= data['check_out']:
            raise serializers.ValidationError("Check-out date must be after check-in date")
        
        listing = self.context['listing']
        if data['guests_count'] > listing.max_guests:
            raise serializers.ValidationError(
                f"Number of guests exceeds maximum allowed ({listing.max_guests})"
            )
        
        return data

class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['listing', 'check_in', 'check_out', 'guests_count', 'special_requests']
        
        
class PaymentInitiationSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    return_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)

class PaymentVerificationSerializer(serializers.Serializer):
    transaction_id = serializers.CharField(max_length=100)

class PaymentSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(source='booking.booking_reference', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_id', 'chapa_transaction_id', 
            'amount', 'currency', 'status', 'payment_url',
            'created_at', 'updated_at', 'booking_reference'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'chapa_transaction_id',
            'status', 'payment_url', 'created_at', 'updated_at'
        ]