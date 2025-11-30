import requests
import json
import logging
from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class ChapaPaymentService:
    def __init__(self):
        self.secret_key = settings.CHAPA_SECRET_KEY
        self.base_url = settings.CHAPA_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
    
    def initiate_payment(self, amount, email, first_name, last_name, 
                        transaction_id, return_url, currency='ETB'):
        """
        Initiate payment with Chapa API
        """
        url = f"{self.base_url}/transaction/initialize"
        
        payload = {
            "amount": str(amount),
            "currency": currency,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": transaction_id,
            "callback_url": return_url,
            "return_url": return_url,
            "customization": {
                "title": "ALX Travel App",
                "description": "Booking Payment"
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                return {
                    'success': True,
                    'payment_url': data['data']['checkout_url'],
                    'transaction_id': data['data']['tx_ref']
                }
            else:
                logger.error(f"Chapa API error: {data.get('message', 'Unknown error')}")
                return {
                    'success': False,
                    'error': data.get('message', 'Failed to initiate payment')
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during payment initiation: {str(e)}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error during payment initiation: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def verify_payment(self, transaction_id):
        """
        Verify payment status with Chapa API
        """
        url = f"{self.base_url}/transaction/verify/{transaction_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                payment_data = data['data']
                return {
                    'success': True,
                    'status': payment_data.get('status'),
                    'chapa_transaction_id': payment_data.get('id'),
                    'amount': payment_data.get('amount'),
                    'currency': payment_data.get('currency'),
                    'payment_method': payment_data.get('payment_method'),
                    'created_at': payment_data.get('created_at')
                }
            else:
                return {
                    'success': False,
                    'error': data.get('message', 'Failed to verify payment')
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during payment verification: {str(e)}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error during payment verification: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }