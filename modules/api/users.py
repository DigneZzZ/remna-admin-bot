import logging
from modules.api.client import RemnaAPI
import re

logger = logging.getLogger(__name__)

class UserAPI:
    """API methods for user management based on Remnawave API v1.6.5"""
    
    # ================================
    # ОСНОВНЫЕ CRUD ОПЕРАЦИИ
    # ================================
    
    @staticmethod
    async def get_all_users():
        """Get all users with pagination support"""
        all_users = []
        start = 0
        size = 500  # Maximum allowed by API
        
        while True:
            # Get batch of users
            params = {
                'size': size,
                'start': start
            }
            
            try:
                response = await RemnaAPI.get("users", params=params)
                
                if not response:
                    break
                
                # Handle different response structures
                users = []
                if isinstance(response, dict):
                    if 'users' in response:
                        users = response['users']
                    elif 'response' in response and 'users' in response['response']:
                        users = response['response']['users']
                    elif 'response' in response and isinstance(response['response'], list):
                        users = response['response']
                elif isinstance(response, list):
                    users = response
                
                if not users:
                    break
                
                all_users.extend(users)
                
                # If we got less than requested size, we've reached the end
                if len(users) < size:
                    break
                
                start += size
                
            except Exception as e:
                logger.error(f"Error fetching users batch (start={start}, size={size}): {e}")
                break
        
        logger.info(f"Retrieved {len(all_users)} users total")
        return {'response': all_users} if all_users else {'response': []}
    
    @staticmethod
    async def get_users_count():
        """Get total number of users efficiently"""
        try:
            # Try to get just first page to check total count
            params = {'size': 1, 'start': 0}
            response = await RemnaAPI.get("users", params=params)
            
            if response and isinstance(response, dict):
                # If API returns total count in response
                if 'total' in response:
                    return response['total']
                elif 'count' in response:
                    return response['count']
            
            # Fallback: get all users and count them
            all_users_response = await UserAPI.get_all_users()
            if all_users_response and 'response' in all_users_response:
                return len(all_users_response['response'])
            
            return 0
        except Exception as e:
            logger.error(f"Error getting users count: {e}")
            return 0
    
    @staticmethod
    async def get_user_by_uuid(uuid):
        """Get user by UUID"""
        return await RemnaAPI.get(f"users/{uuid}")
    
    @staticmethod
    async def get_user_by_short_uuid(short_uuid):
        """Get user by short UUID"""
        return await RemnaAPI.get(f"users/by-short-uuid/{short_uuid}")
    
    @staticmethod
    async def get_user_by_subscription_uuid(subscription_uuid):
        """Get user by subscription UUID"""
        return await RemnaAPI.get(f"users/by-subscription-uuid/{subscription_uuid}")
    
    @staticmethod
    async def get_user_by_username(username):
        """Get user by username"""
        return await RemnaAPI.get(f"users/by-username/{username}")
    
    @staticmethod
    async def create_user(user_data):
        """
        Create a new user
        
        Required fields:
        - username: Username (6-34 chars, alphanumeric, underscore, hyphen)
        - trafficLimitStrategy: NO_RESET, DAY, WEEK, MONTH
        - expireAt: ISO 8601 date string
        
        Optional fields:
        - description: User description
        - trafficLimitBytes: Traffic limit in bytes
        - hwidDeviceLimit: Device limit (requires NO_RESET strategy)
        - email: Email address
        - tag: User tag (1-16 chars, uppercase alphanumeric + underscore)
        - telegramId: Telegram user ID
        - activeUserInbounds: List of inbound configurations
        """
        # Validate required fields
        required_fields = ["username", "trafficLimitStrategy", "expireAt"]
        for field in required_fields:
            if field not in user_data:
                logger.error(f"Missing required field: {field}")
                return None
        
        # Validate username format
        if not re.match(r"^[a-zA-Z0-9_-]{6,34}$", user_data["username"]):
            logger.error(f"Invalid username format: {user_data['username']}")
            return None
            
        # Validate tag format if provided
        if "tag" in user_data and user_data["tag"] and not re.match(r"^[A-Z0-9_]{1,16}$", user_data["tag"]):
            logger.error(f"Invalid tag format: {user_data['tag']}")
            return None
            
        # Validate traffic limit strategy
        valid_strategies = ["NO_RESET", "DAY", "WEEK", "MONTH"]
        if user_data["trafficLimitStrategy"] not in valid_strategies:
            logger.error(f"Invalid traffic limit strategy: '{user_data['trafficLimitStrategy']}'")
            return None
        
        # If HWID device limit is set, strategy must be NO_RESET
        if "hwidDeviceLimit" in user_data and user_data.get("hwidDeviceLimit", 0) > 0:
            if user_data.get("trafficLimitStrategy") != "NO_RESET":
                logger.warning(f"Changing trafficLimitStrategy to NO_RESET because hwidDeviceLimit is set")
                user_data["trafficLimitStrategy"] = "NO_RESET"
        
        # Validate numeric fields
        if "trafficLimitBytes" in user_data and user_data["trafficLimitBytes"] < 0:
            logger.error(f"Invalid traffic limit: {user_data['trafficLimitBytes']}")
            return None
            
        if "hwidDeviceLimit" in user_data and user_data["hwidDeviceLimit"] < 0:
            logger.error(f"Invalid HWID device limit: {user_data['hwidDeviceLimit']}")
            return None
        
        # Validate email format if provided
        if "email" in user_data and user_data["email"]:
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user_data["email"]):
                logger.error(f"Invalid email format: {user_data['email']}")
                return None
        
        logger.debug(f"Creating user with data: {user_data}")
        return await RemnaAPI.post("users", user_data)
    
    @staticmethod
    async def update_user(uuid, update_data):
        """Update a user"""
        # Add UUID to update data
        update_data["uuid"] = uuid
        logger.debug(f"Updating user {uuid} with data: {update_data}")
        return await RemnaAPI.patch("users", update_data)
    
    @staticmethod
    async def delete_user(uuid):
        """Delete a user"""
        return await RemnaAPI.delete(f"users/{uuid}")
    
    # ================================
    # ДЕЙСТВИЯ С ПОЛЬЗОВАТЕЛЯМИ
    # ================================
    
    @staticmethod
    async def revoke_user_subscription(uuid):
        """Revoke user subscription"""
        return await RemnaAPI.post(f"users/{uuid}/actions/revoke")
    
    @staticmethod
    async def reset_user_traffic(uuid):
        """Reset user traffic"""
        return await RemnaAPI.post(f"users/{uuid}/actions/reset-traffic")
    
    @staticmethod
    async def activate_all_inbounds(uuid):
        """Activate all inbounds for a user"""
        return await RemnaAPI.post(f"users/{uuid}/actions/activate-all-inbounds")
    
    @staticmethod
    async def disable_user(uuid):
        """Disable a user"""
        return await RemnaAPI.patch("users", {"uuid": uuid, "status": "DISABLED"})
    
    @staticmethod
    async def enable_user(uuid):
        """Enable a user"""
        return await RemnaAPI.patch("users", {"uuid": uuid, "status": "ACTIVE"})
    
    # ================================
    # МАССОВЫЕ ОПЕРАЦИИ
    # ================================
    
    @staticmethod
    async def bulk_delete_users(uuids):
        """Bulk delete users by UUIDs"""
        data = {"uuids": uuids}
        return await RemnaAPI.post("users/bulk/delete", data)
    
    @staticmethod
    async def bulk_delete_users_by_status(status):
        """Bulk delete users by status"""
        data = {"status": status}
        return await RemnaAPI.post("users/bulk/delete-by-status", data)
    
    @staticmethod
    async def bulk_revoke_users_subscription(uuids):
        """Bulk revoke users subscription"""
        data = {"uuids": uuids}
        return await RemnaAPI.post("users/bulk/revoke-subscription", data)
    
    @staticmethod
    async def bulk_reset_users_traffic(uuids):
        """Bulk reset users traffic"""
        data = {"uuids": uuids}
        return await RemnaAPI.post("users/bulk/reset-traffic", data)
    
    @staticmethod
    async def bulk_update_users(uuids, fields):
        """Bulk update users"""
        data = {
            "uuids": uuids,
            "fields": fields
        }
        return await RemnaAPI.post("users/bulk/update", data)
    
    @staticmethod
    async def bulk_update_users_inbounds(uuids, inbounds):
        """Bulk update users inbounds"""
        data = {
            "uuids": uuids,
            "activeUserInbounds": inbounds
        }
        return await RemnaAPI.post("users/bulk/update-inbounds", data)
    
    # ================================
    # СТАТИСТИКА И МОНИТОРИНГ
    # ================================
    
    @staticmethod
    async def get_user_usage_by_range(uuid, start_date, end_date):
        """Get user usage by date range"""
        params = {
            "start": start_date,
            "end": end_date
        }
        return await RemnaAPI.get(f"users/stats/usage/{uuid}/range", params)
    
    @staticmethod
    async def get_users_usage_by_range(start_date, end_date):
        """Get all users usage by date range"""
        params = {
            "start": start_date,
            "end": end_date
        }
        return await RemnaAPI.get("users/stats/usage/range", params)
    
    @staticmethod
    async def get_users_realtime_usage():
        """Get users realtime usage"""
        return await RemnaAPI.get("users/stats/usage/realtime")
    
    # ================================
    # HWID УПРАВЛЕНИЕ (ОФИЦИАЛЬНЫЕ ENDPOINTS)
    # ================================
    
    @staticmethod
    async def get_user_hwid_devices(uuid):
        """Get user HWID devices"""
        return await RemnaAPI.get(f"hwid/devices/{uuid}")
    
    @staticmethod
    async def add_user_hwid_device(uuid, hwid, platform=None, os_version=None, device_model=None, user_agent=None):
        """Add a HWID device to a user"""
        data = {
            "userUuid": uuid,
            "hwid": hwid
        }
        
        if platform:
            data["platform"] = platform
        
        if os_version:
            data["osVersion"] = os_version
        
        if device_model:
            data["deviceModel"] = device_model
        
        if user_agent:
            data["userAgent"] = user_agent
        
        return await RemnaAPI.post("hwid/devices", data)
    
    @staticmethod
    async def delete_user_hwid_device(hwid):
        """Delete a HWID device (исправлен endpoint)"""
        return await RemnaAPI.delete(f"hwid/devices/{hwid}")
    
    # ================================
    # ПОИСК И ФИЛЬТРАЦИЯ (КЛИЕНТСКАЯ ОБРАБОТКА)
    # ================================
    
    @staticmethod
    async def search_users_by_partial_name(partial_name):
        """Search users by partial name match (client-side filtering)"""
        try:
            response = await UserAPI.get_all_users()
            if not response or 'response' not in response:
                return {'response': []}
            
            users = response['response']
            if not users:
                return {'response': []}
            
            partial_name_lower = partial_name.lower()
            matching_users = []
            
            for user in users:
                if partial_name_lower in user.get("username", "").lower():
                    matching_users.append(user)
            
            return {'response': matching_users}
        except Exception as e:
            logger.error(f"Error searching users by partial name: {e}")
            return {'response': []}
    
    @staticmethod
    async def search_users_by_description(description_keyword):
        """Search users by description keyword (client-side filtering)"""
        try:
            response = await UserAPI.get_all_users()
            if not response or 'response' not in response:
                return {'response': []}
            
            users = response['response']
            if not users:
                return {'response': []}
            
            keyword_lower = description_keyword.lower()
            matching_users = []
            
            for user in users:
                user_description = user.get("description", "")
                if user_description and keyword_lower in user_description.lower():
                    matching_users.append(user)
            
            return {'response': matching_users}
        except Exception as e:
            logger.error(f"Error searching users by description: {e}")
            return {'response': []}
    
    @staticmethod
    async def get_user_by_telegram_id(telegram_id):
        """Get user by Telegram ID (client-side filtering)"""
        try:
            response = await UserAPI.get_all_users()
            if not response or 'response' not in response:
                return {'response': []}
            
            users = response['response']
            for user in users:
                if user.get("telegramId") == telegram_id:
                    # Возвращаем найденного пользователя в виде списка с одним элементом
                    return {'response': [user]}
            
            return {'response': []}
        except Exception as e:
            logger.error(f"Error getting user by telegram ID: {e}")
            return {'response': []}
    
    @staticmethod
    async def get_user_by_email(email):
        """Get user by email (client-side filtering)"""
        try:
            response = await UserAPI.get_all_users()
            if not response or 'response' not in response:
                return []
            
            users = response['response']
            for user in users:
                if user.get("email") == email:
                    return {"response": user}
            
            return []
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return []
    
    @staticmethod
    async def get_user_by_tag(tag):
        """Get user by tag (client-side filtering)"""
        try:
            response = await UserAPI.get_all_users()
            if not response or 'response' not in response:
                return []
            
            users = response['response']
            for user in users:
                if user.get("tag") == tag:
                    return {"response": user}
            
            return []
        except Exception as e:
            logger.error(f"Error getting user by tag: {e}")
            return []
    
    @staticmethod
    async def get_users_by_status(status):
        """Get users by status (client-side filtering)"""
        try:
            response = await UserAPI.get_all_users()
            if not response or 'response' not in response:
                return {'response': []}
            
            users = response['response']
            filtered_users = [user for user in users if user.get('status') == status]
            
            return {'response': filtered_users}
        except Exception as e:
            logger.error(f"Error getting users by status: {e}")
            return {'response': []}
    
    @staticmethod
    async def get_active_users():
        """Get active users"""
        return await UserAPI.get_users_by_status("ACTIVE")
    
    @staticmethod
    async def get_disabled_users():
        """Get disabled users"""
        return await UserAPI.get_users_by_status("DISABLED")
    
    @staticmethod
    async def get_limited_users():
        """Get limited users"""
        return await UserAPI.get_users_by_status("LIMITED")
    
    @staticmethod
    async def get_expired_users():
        """Get expired users"""
        return await UserAPI.get_users_by_status("EXPIRED")
    
    # ================================
    # СТАТИСТИКА ДЛЯ БОТА
    # ================================
    
    @staticmethod
    async def get_users_stats():
        """Get user statistics efficiently"""
        try:
            response = await UserAPI.get_all_users()
            
            stats = {'ACTIVE': 0, 'DISABLED': 0, 'LIMITED': 0, 'EXPIRED': 0}
            total_traffic = 0
            users = []
            
            if response and 'response' in response:
                users = response['response']
                
                for user in users:
                    status = user.get('status', 'UNKNOWN')
                    if status in stats:
                        stats[status] += 1
                    
                    # Calculate traffic
                    traffic_used = user.get('trafficUsed', 0)
                    if isinstance(traffic_used, (int, float)):
                        total_traffic += traffic_used
            
            return {
                'count': len(users),
                'stats': stats,
                'total_traffic': total_traffic
            }
        except Exception as e:
            logger.error(f"Error getting users stats: {e}")
            return {
                'count': 0,
                'stats': {'ACTIVE': 0, 'DISABLED': 0, 'LIMITED': 0, 'EXPIRED': 0},
                'total_traffic': 0
            }
    
    # ================================
    # ВАЛИДАЦИЯ И УТИЛИТЫ
    # ================================
    
    @staticmethod
    def validate_user_data(data):
        """
        Validate user data before sending to API
        
        Returns:
            tuple: (is_valid, error_message)
        """
        required_fields = ['username', 'trafficLimitStrategy', 'expireAt']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        
        # Validate username
        if not re.match(r"^[a-zA-Z0-9_-]{6,34}$", data["username"]):
            return False, "Username must be 6-34 characters, alphanumeric, underscore, or hyphen"
        
        # Validate strategy
        valid_strategies = ["NO_RESET", "DAY", "WEEK", "MONTH"]
        if data["trafficLimitStrategy"] not in valid_strategies:
            return False, f"Traffic limit strategy must be one of: {', '.join(valid_strategies)}"
        
        # Validate tag if provided
        if "tag" in data and data["tag"]:
            if not re.match(r"^[A-Z0-9_]{1,16}$", data["tag"]):
                return False, "Tag must be 1-16 characters, uppercase alphanumeric or underscore"
        
        # Validate email if provided
        if "email" in data and data["email"]:
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", data["email"]):
                return False, "Invalid email format"
        
        # HWID device limit requires NO_RESET strategy
        if data.get("hwidDeviceLimit", 0) > 0 and data["trafficLimitStrategy"] != "NO_RESET":
            return False, "HWID device limit requires NO_RESET traffic strategy"
        
        return True, None
    
    @staticmethod
    def create_user_template(username, expire_days=30, traffic_gb=None, **kwargs):
        """
        Create a user data template with default values
        
        Args:
            username: Username for the user
            expire_days: Days until expiration (default: 30)
            traffic_gb: Traffic limit in GB (optional)
            **kwargs: Additional optional parameters
        
        Returns:
            dict: User data ready for API
        """
        from datetime import datetime, timedelta
        
        # Calculate expiration date
        expire_date = datetime.now() + timedelta(days=expire_days)
        
        user_data = {
            "username": username,
            "trafficLimitStrategy": kwargs.get("trafficLimitStrategy", "MONTH"),
            "expireAt": expire_date.isoformat() + "Z"
        }
        
        # Add traffic limit if specified
        if traffic_gb:
            user_data["trafficLimitBytes"] = traffic_gb * 1024 * 1024 * 1024
        
        # Add optional fields if provided
        optional_fields = ['description', 'email', 'tag', 'telegramId', 'hwidDeviceLimit', 'activeUserInbounds']
        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                user_data[field] = kwargs[field]
        
        return user_data