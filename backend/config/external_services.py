import asyncio
import time
import random
from typing import Dict, List, Any


class MockStoreServices:
    """Mock implementations of Israeli store integrations"""

    @staticmethod
    async def wolt_order_simulation(items: List[Dict]) -> Dict:
        """Simulate Wolt ordering with realistic delay"""
        # Simulate API delay
        await asyncio.sleep(random.uniform(2, 3))

        total_price = sum(item.get('quantity', 1) *
                          random.uniform(5, 50) for item in items)

        return {
            'success': True,
            'order_id': f'WOLT-{int(time.time())}',
            'estimated_delivery': '30-45 minutes',
            'total_price_nis': round(total_price, 2),
            'items': [
                {
                    **item,
                    'price_nis': round(random.uniform(5, 50), 2),
                    # 66% availability
                    'available': random.choice([True, True, False])
                }
                for item in items
            ],
            'delivery_fee_nis': 15.90,
            'store': 'Super-Pharm Express'
        }

    @staticmethod
    async def shufersal_price_check(items: List[str]) -> Dict:
        """Mock Shufersal price checking"""
        await asyncio.sleep(random.uniform(1, 2))

        mock_prices = {
            'milk': 6.90,
            'bread': 12.50,
            'eggs': 15.90,
            'chicken': 35.90,
            'rice': 8.90,
            'pasta': 7.50,
            'tomatoes': 4.90,
            'cucumber': 3.90,
            'cheese': 22.90,
            'yogurt': 4.50
        }

        results = []
        for item in items:
            base_item = item.lower().split()[0]  # Simple parsing
            price = mock_prices.get(base_item, random.uniform(5, 30))
            results.append({
                'item': item,
                'price_nis': round(price, 2),
                'unit': 'unit',
                # 75% in stock
                'in_stock': random.choice([True, True, True, False]),
                'promotion': random.choice([None, '2+1', '20% off', None, None])
            })

        return {
            'store': 'Shufersal Deal',
            'location': 'Petah Tikva',
            'prices': results,
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }

    @staticmethod
    async def nutrition_database_lookup(food_name: str) -> Dict:
        """Mock nutrition database lookup"""
        await asyncio.sleep(0.5)

        # Common foods nutrition data
        nutrition_db = {
            'apple': {'calories': 52, 'protein': 0.3, 'carbs': 14, 'fat': 0.2, 'fiber': 2.4},
            'banana': {'calories': 89, 'protein': 1.1, 'carbs': 23, 'fat': 0.3, 'fiber': 2.6},
            'chicken breast': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6, 'fiber': 0},
            'salmon': {'calories': 208, 'protein': 20, 'carbs': 0, 'fat': 13, 'fiber': 0},
            'rice': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3, 'fiber': 0.4},
            'pasta': {'calories': 131, 'protein': 5, 'carbs': 25, 'fat': 1.1, 'fiber': 1.8},
            'broccoli': {'calories': 55, 'protein': 3.7, 'carbs': 11, 'fat': 0.6, 'fiber': 5.1},
            'milk': {'calories': 42, 'protein': 3.4, 'carbs': 5, 'fat': 1, 'fiber': 0},
            'egg': {'calories': 155, 'protein': 13, 'carbs': 1.1, 'fat': 11, 'fiber': 0},
            'bread': {'calories': 265, 'protein': 9, 'carbs': 49, 'fat': 3.2, 'fiber': 2.7}
        }

        # Check if food exists in database
        food_key = food_name.lower()
        if food_key in nutrition_db:
            return {
                'found': True,
                'food_name': food_name,
                'serving_size': '100g',
                'nutrition': nutrition_db[food_key],
                'source': 'USDA Database'
            }

        # Generate random nutrition for unknown foods
        return {
            'found': False,
            'food_name': food_name,
            'serving_size': '100g',
            'nutrition': {
                'calories': random.randint(50, 300),
                'protein': round(random.uniform(0, 30), 1),
                'carbs': round(random.uniform(0, 50), 1),
                'fat': round(random.uniform(0, 20), 1),
                'fiber': round(random.uniform(0, 10), 1)
            },
            'source': 'Estimated'
        }
