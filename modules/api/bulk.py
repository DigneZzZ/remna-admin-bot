from modules.api.client import RemnaAPI

class BulkAPI:
    """API methods for bulk operations based on Remnawave API v1.6.5"""
    
    # ================================
    # ПОЛЬЗОВАТЕЛИ (USERS) - Массовые операции
    # ================================
    
    @staticmethod
    async def bulk_delete_users(uuids):
        """
        Bulk delete users by UUIDs
        
        Args:
            uuids: List of user UUIDs to delete
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("users/bulk/delete", data)
    
    @staticmethod
    async def bulk_delete_users_by_status(status):
        """
        Bulk delete users by status
        
        Args:
            status: User status (ACTIVE, EXPIRED, LIMITED, DISABLED)
        """
        data = {"status": status}
        return await RemnaAPI.post("users/bulk/delete-by-status", data)
    
    @staticmethod
    async def bulk_revoke_users_subscription(uuids):
        """
        Bulk revoke users subscription by UUIDs
        
        Args:
            uuids: List of user UUIDs
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("users/bulk/revoke-subscription", data)
    
    @staticmethod
    async def bulk_reset_users_traffic(uuids):
        """
        Bulk reset traffic for users by UUIDs
        
        Args:
            uuids: List of user UUIDs
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("users/bulk/reset-traffic", data)
    
    @staticmethod
    async def bulk_update_users(uuids, fields):
        """
        Bulk update users by UUIDs
        
        Args:
            uuids: List of user UUIDs
            fields: Dictionary with fields to update
        """
        data = {
            "uuids": uuids,
            "fields": fields
        }
        return await RemnaAPI.post("users/bulk/update", data)
    
    @staticmethod
    async def bulk_update_users_inbounds(uuids, inbounds):
        """
        Bulk update users inbounds by UUIDs
        
        Args:
            uuids: List of user UUIDs
            inbounds: List of inbound configurations
        """
        data = {
            "uuids": uuids,
            "activeUserInbounds": inbounds
        }
        return await RemnaAPI.post("users/bulk/update-inbounds", data)
    
    @staticmethod
    async def bulk_update_all_users(fields):
        """
        Bulk update all users
        
        Args:
            fields: Dictionary with fields to update for all users
        """
        return await RemnaAPI.post("users/bulk/all/update", fields)
    
    @staticmethod
    async def bulk_reset_all_users_traffic():
        """Bulk reset all users traffic"""
        return await RemnaAPI.post("users/bulk/all/reset-traffic")
    
    @staticmethod
    async def bulk_revoke_all_users_subscription():
        """Bulk revoke all users subscription"""
        return await RemnaAPI.post("users/bulk/all/revoke-subscription")
    
    @staticmethod
    async def bulk_delete_all_users():
        """Bulk delete all users"""
        return await RemnaAPI.post("users/bulk/all/delete")
    
    # ================================
    # INBOUND'Ы - Массовые операции
    # ================================
    
    @staticmethod
    async def bulk_delete_inbounds(uuids):
        """
        Bulk delete inbounds by UUIDs
        
        Args:
            uuids: List of inbound UUIDs to delete
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("inbounds/bulk/delete", data)
    
    @staticmethod
    async def bulk_enable_inbounds(uuids):
        """
        Bulk enable inbounds by UUIDs
        
        Args:
            uuids: List of inbound UUIDs to enable
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("inbounds/bulk/enable", data)
    
    @staticmethod
    async def bulk_disable_inbounds(uuids):
        """
        Bulk disable inbounds by UUIDs
        
        Args:
            uuids: List of inbound UUIDs to disable
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("inbounds/bulk/disable", data)
    
    @staticmethod
    async def bulk_restart_inbounds(uuids):
        """
        Bulk restart inbounds by UUIDs
        
        Args:
            uuids: List of inbound UUIDs to restart
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("inbounds/bulk/restart", data)
    
    @staticmethod
    async def bulk_add_inbound_to_users(inbound_uuid, user_uuids):
        """
        Add inbound to multiple users
        
        Args:
            inbound_uuid: UUID of the inbound
            user_uuids: List of user UUIDs
        """
        data = {
            "inboundUuid": inbound_uuid,
            "userUuids": user_uuids
        }
        return await RemnaAPI.post("inbounds/bulk/add-to-users", data)
    
    @staticmethod
    async def bulk_remove_inbound_from_users(inbound_uuid, user_uuids):
        """
        Remove inbound from multiple users
        
        Args:
            inbound_uuid: UUID of the inbound
            user_uuids: List of user UUIDs
        """
        data = {
            "inboundUuid": inbound_uuid,
            "userUuids": user_uuids
        }
        return await RemnaAPI.post("inbounds/bulk/remove-from-users", data)
    
    @staticmethod
    async def bulk_add_inbound_to_nodes(inbound_uuid, node_uuids):
        """
        Add inbound to multiple nodes
        
        Args:
            inbound_uuid: UUID of the inbound
            node_uuids: List of node UUIDs
        """
        data = {
            "inboundUuid": inbound_uuid,
            "nodeUuids": node_uuids
        }
        return await RemnaAPI.post("inbounds/bulk/add-to-nodes", data)
    
    @staticmethod
    async def bulk_remove_inbound_from_nodes(inbound_uuid, node_uuids):
        """
        Remove inbound from multiple nodes
        
        Args:
            inbound_uuid: UUID of the inbound
            node_uuids: List of node UUIDs
        """
        data = {
            "inboundUuid": inbound_uuid,
            "nodeUuids": node_uuids
        }
        return await RemnaAPI.post("inbounds/bulk/remove-from-nodes", data)
    
    # ================================
    # ХОСТЫ - Массовые операции
    # ================================
    
    @staticmethod
    async def bulk_delete_hosts(uuids):
        """
        Bulk delete hosts by UUIDs
        
        Args:
            uuids: List of host UUIDs to delete
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("hosts/bulk/delete", data)
    
    @staticmethod
    async def bulk_enable_hosts(uuids):
        """
        Bulk enable hosts by UUIDs
        
        Args:
            uuids: List of host UUIDs to enable
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("hosts/bulk/enable", data)
    
    @staticmethod
    async def bulk_disable_hosts(uuids):
        """
        Bulk disable hosts by UUIDs
        
        Args:
            uuids: List of host UUIDs to disable
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("hosts/bulk/disable", data)
    
    @staticmethod
    async def bulk_set_hosts_inbound(uuids, inbound_uuid):
        """
        Set inbound for multiple hosts
        
        Args:
            uuids: List of host UUIDs
            inbound_uuid: UUID of the inbound to set
        """
        data = {
            "uuids": uuids,
            "inboundUuid": inbound_uuid
        }
        return await RemnaAPI.post("hosts/bulk/set-inbound", data)
    
    @staticmethod
    async def bulk_set_hosts_port(uuids, port):
        """
        Set port for multiple hosts
        
        Args:
            uuids: List of host UUIDs
            port: Port number (1-65535)
        """
        data = {
            "uuids": uuids,
            "port": port
        }
        return await RemnaAPI.post("hosts/bulk/set-port", data)
    
    # ================================
    # НОДЫ - Массовые операции
    # ================================
    
    @staticmethod
    async def bulk_delete_nodes(uuids):
        """
        Bulk delete nodes by UUIDs
        
        Args:
            uuids: List of node UUIDs to delete
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("nodes/bulk/delete", data)
    
    @staticmethod
    async def bulk_enable_nodes(uuids):
        """
        Bulk enable nodes by UUIDs
        
        Args:
            uuids: List of node UUIDs to enable
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("nodes/bulk/enable", data)
    
    @staticmethod
    async def bulk_disable_nodes(uuids):
        """
        Bulk disable nodes by UUIDs
        
        Args:
            uuids: List of node UUIDs to disable
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("nodes/bulk/disable", data)
    
    @staticmethod
    async def bulk_restart_nodes(uuids):
        """
        Bulk restart nodes by UUIDs
        
        Args:
            uuids: List of node UUIDs to restart
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("nodes/bulk/restart", data)
    
    # ================================
    # УТИЛИТАРНЫЕ МЕТОДЫ
    # ================================
    
    @staticmethod
    def validate_bulk_operation_data(operation_type, data):
        """
        Validate bulk operation data
        
        Args:
            operation_type: Type of operation (users, inbounds, hosts, nodes)
            data: Data to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if operation_type == "users":
            return BulkAPI._validate_user_bulk_data(data)
        elif operation_type == "inbounds":
            return BulkAPI._validate_inbound_bulk_data(data)
        elif operation_type == "hosts":
            return BulkAPI._validate_host_bulk_data(data)
        elif operation_type == "nodes":
            return BulkAPI._validate_node_bulk_data(data)
        else:
            return False, f"Unknown operation type: {operation_type}"
    
    @staticmethod
    def _validate_user_bulk_data(data):
        """Validate user bulk operation data"""
        if "uuids" in data:
            if not isinstance(data["uuids"], list) or not data["uuids"]:
                return False, "UUIDs must be a non-empty list"
        
        if "status" in data:
            valid_statuses = ["ACTIVE", "EXPIRED", "LIMITED", "DISABLED"]
            if data["status"] not in valid_statuses:
                return False, f"Status must be one of: {', '.join(valid_statuses)}"
        
        if "fields" in data:
            if not isinstance(data["fields"], dict):
                return False, "Fields must be a dictionary"
        
        return True, None
    
    @staticmethod
    def _validate_inbound_bulk_data(data):
        """Validate inbound bulk operation data"""
        if "uuids" in data:
            if not isinstance(data["uuids"], list) or not data["uuids"]:
                return False, "UUIDs must be a non-empty list"
        
        if "inboundUuid" in data:
            if not data["inboundUuid"]:
                return False, "Inbound UUID is required"
        
        if "userUuids" in data:
            if not isinstance(data["userUuids"], list):
                return False, "User UUIDs must be a list"
        
        if "nodeUuids" in data:
            if not isinstance(data["nodeUuids"], list):
                return False, "Node UUIDs must be a list"
        
        return True, None
    
    @staticmethod
    def _validate_host_bulk_data(data):
        """Validate host bulk operation data"""
        if "uuids" in data:
            if not isinstance(data["uuids"], list) or not data["uuids"]:
                return False, "UUIDs must be a non-empty list"
        
        if "port" in data:
            port = data["port"]
            if not isinstance(port, int) or port < 1 or port > 65535:
                return False, "Port must be between 1 and 65535"
        
        if "inboundUuid" in data:
            if not data["inboundUuid"]:
                return False, "Inbound UUID is required"
        
        return True, None
    
    @staticmethod
    def _validate_node_bulk_data(data):
        """Validate node bulk operation data"""
        if "uuids" in data:
            if not isinstance(data["uuids"], list) or not data["uuids"]:
                return False, "UUIDs must be a non-empty list"
        
        return True, None
    
    # ================================
    # КОМБИНИРОВАННЫЕ ОПЕРАЦИИ
    # ================================
    
    @staticmethod
    async def bulk_operation_with_validation(operation_func, operation_type, data):
        """
        Execute bulk operation with validation
        
        Args:
            operation_func: Function to execute
            operation_type: Type of operation for validation
            data: Data for operation
            
        Returns:
            API response or error
        """
        is_valid, error = BulkAPI.validate_bulk_operation_data(operation_type, data)
        if not is_valid:
            return {"error": error, "success": False}
        
        try:
            return await operation_func
        except Exception as e:
            return {"error": str(e), "success": False}
    
    @staticmethod
    async def execute_multiple_bulk_operations(operations):
        """
        Execute multiple bulk operations sequentially
        
        Args:
            operations: List of operation dictionaries with 'func' and 'args' keys
            
        Returns:
            List of results
        """
        results = []
        for operation in operations:
            try:
                func = operation['func']
                args = operation.get('args', [])
                kwargs = operation.get('kwargs', {})
                result = await func(*args, **kwargs)
                results.append({"success": True, "result": result})
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        
        return results
    
    # ================================
    # СТАТИСТИКА И МОНИТОРИНГ МАССОВЫХ ОПЕРАЦИЙ
    # ================================
    
    @staticmethod
    def create_bulk_operation_summary(operation_name, total_items, successful_items=None, failed_items=None):
        """
        Create summary for bulk operation
        
        Args:
            operation_name: Name of the operation
            total_items: Total number of items processed
            successful_items: Number of successful operations
            failed_items: Number of failed operations
            
        Returns:
            Dictionary with operation summary
        """
        summary = {
            "operation": operation_name,
            "total_items": total_items,
            "timestamp": None  # Would be set by calling code
        }
        
        if successful_items is not None:
            summary["successful_items"] = successful_items
        
        if failed_items is not None:
            summary["failed_items"] = failed_items
        
        if successful_items is not None and failed_items is not None:
            summary["success_rate"] = (successful_items / total_items) * 100 if total_items > 0 else 0
        
        return summary