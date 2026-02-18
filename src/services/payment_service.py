import base64
import hashlib
import json
import urllib.parse
from typing import Dict, Any
from config import settings

class LiqPayService:
    """Service for LiqPay payment integration."""
    
    @staticmethod
    def generate_payment_data(order_id: str, amount: int, description: str) -> Dict[str, str]:
        """Generate data and signature for LiqPay checkout.
        
        Returns:
            Dict containing 'data' and 'signature'
        """
        params = {
            "version": 3,
            "public_key": settings.liqpay_public_key,
            "action": "pay",
            "amount": float(amount),
            "currency": "UAH",
            "description": description,
            "order_id": order_id,
        }
        
        json_params = json.dumps(params).encode('utf-8')
        data = base64.b64encode(json_params).decode('utf-8')
        
        # signature = base64(sha1(private_key + data + private_key))
        sign_string = settings.liqpay_private_key + data + settings.liqpay_private_key
        sha1_hash = hashlib.sha1(sign_string.encode('utf-8')).digest()
        signature = base64.b64encode(sha1_hash).decode('utf-8')
        
        return {
            "data": data,
            "signature": signature
        }

    @staticmethod
    def get_payment_url(order_id: str, amount: int, description: str) -> str:
        """Generate full LiqPay checkout URL."""
        params = LiqPayService.generate_payment_data(order_id, amount, description)
        data_quoted = urllib.parse.quote(params['data'])
        signature_quoted = urllib.parse.quote(params['signature'])
        return f"https://www.liqpay.ua/api/3/checkout?data={data_quoted}&signature={signature_quoted}"

payment_service = LiqPayService()
