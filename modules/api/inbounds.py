from modules.api.client import RemnaAPI

class InboundAPI:
    """API methods for inbound management based on Remnawave API v1.6.5"""
    
    # Основные CRUD операции
    @staticmethod
    async def get_all_inbounds():
        """Get all inbounds"""
        return await RemnaAPI.get("inbounds")
    
    @staticmethod
    async def get_inbound_by_uuid(uuid):
        """Get inbound by UUID"""
        return await RemnaAPI.get(f"inbounds/{uuid}")
    
    @staticmethod
    async def create_inbound(data):
        """
        Create a new inbound
        
        Required fields:
        - tag: Inbound tag/name (string)
        - protocol: Protocol type (vless, vmess, trojan, shadowsocks)
        - port: Port number (integer, 1-65535)
        - listen: Listen address (default: "0.0.0.0")
        
        Optional fields depend on protocol:
        - settings: Protocol-specific settings
        - streamSettings: Stream configuration
        - sniffing: Sniffing configuration
        - allocate: Port allocation settings
        """
        return await RemnaAPI.post("inbounds", data)
    
    @staticmethod
    async def update_inbound(data):
        """
        Update an inbound
        
        Required field:
        - uuid: Inbound UUID
        
        Optional fields (same as create_inbound):
        - tag, protocol, port, listen, settings, streamSettings, sniffing, allocate
        """
        return await RemnaAPI.patch("inbounds", data)
    
    @staticmethod
    async def delete_inbound(uuid):
        """Delete an inbound by UUID"""
        return await RemnaAPI.delete(f"inbounds/{uuid}")
    
    # Управление состоянием
    @staticmethod
    async def enable_inbound(uuid):
        """Enable inbound"""
        return await RemnaAPI.post(f"inbounds/{uuid}/enable")
    
    @staticmethod
    async def disable_inbound(uuid):
        """Disable inbound"""
        return await RemnaAPI.post(f"inbounds/{uuid}/disable")
    
    @staticmethod
    async def restart_inbound(uuid):
        """Restart inbound"""
        return await RemnaAPI.post(f"inbounds/{uuid}/restart")
    
    # Операции с порядком
    @staticmethod
    async def reorder_inbounds(inbounds_data):
        """
        Reorder inbounds
        
        Args:
            inbounds_data: List of objects with 'uuid' and 'viewPosition' fields
            Example: [{"uuid": "inbound-uuid-1", "viewPosition": 1}, ...]
        """
        data = {"inbounds": inbounds_data}
        return await RemnaAPI.post("inbounds/actions/reorder", data)
    
    # Массовые операции
    @staticmethod
    async def bulk_delete_inbounds(uuids):
        """
        Delete multiple inbounds by UUIDs
        
        Args:
            uuids: List of inbound UUIDs to delete
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("inbounds/bulk/delete", data)
    
    @staticmethod
    async def bulk_enable_inbounds(uuids):
        """
        Enable multiple inbounds by UUIDs
        
        Args:
            uuids: List of inbound UUIDs to enable
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("inbounds/bulk/enable", data)
    
    @staticmethod
    async def bulk_disable_inbounds(uuids):
        """
        Disable multiple inbounds by UUIDs
        
        Args:
            uuids: List of inbound UUIDs to disable
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("inbounds/bulk/disable", data)
    
    @staticmethod
    async def bulk_restart_inbounds(uuids):
        """
        Restart multiple inbounds by UUIDs
        
        Args:
            uuids: List of inbound UUIDs to restart
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("inbounds/bulk/restart", data)
    
    # Операции с пользователями
    @staticmethod
    async def add_inbound_to_users(inbound_uuid, user_uuids):
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
    async def remove_inbound_from_users(inbound_uuid, user_uuids):
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
    async def add_inbound_to_user(inbound_uuid, user_uuid):
        """Add inbound to specific user"""
        return await InboundAPI.add_inbound_to_users(inbound_uuid, [user_uuid])
    
    @staticmethod
    async def remove_inbound_from_user(inbound_uuid, user_uuid):
        """Remove inbound from specific user"""
        return await InboundAPI.remove_inbound_from_users(inbound_uuid, [user_uuid])
    
    # Операции с нодами
    @staticmethod
    async def add_inbound_to_nodes(inbound_uuid, node_uuids):
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
    async def remove_inbound_from_nodes(inbound_uuid, node_uuids):
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
    
    @staticmethod
    async def add_inbound_to_node(inbound_uuid, node_uuid):
        """Add inbound to specific node"""
        return await InboundAPI.add_inbound_to_nodes(inbound_uuid, [node_uuid])
    
    @staticmethod
    async def remove_inbound_from_node(inbound_uuid, node_uuid):
        """Remove inbound from specific node"""
        return await InboundAPI.remove_inbound_from_nodes(inbound_uuid, [node_uuid])
    
    # Конфигурация и связанные данные
    @staticmethod
    async def get_inbound_users(inbound_uuid):
        """Get users associated with inbound"""
        return await RemnaAPI.get(f"inbounds/{inbound_uuid}/users")
    
    @staticmethod
    async def get_inbound_nodes(inbound_uuid):
        """Get nodes associated with inbound"""
        return await RemnaAPI.get(f"inbounds/{inbound_uuid}/nodes")
    
    @staticmethod
    async def get_inbound_hosts(inbound_uuid):
        """Get hosts associated with inbound"""
        return await RemnaAPI.get(f"inbounds/{inbound_uuid}/hosts")
    
    # Дополнительные утилитарные методы (клиентская фильтрация)
    @staticmethod
    async def get_inbounds_by_protocol(protocol):
        """
        Get inbounds by protocol (client-side filtering)
        
        Args:
            protocol: Protocol name (vless, vmess, trojan, shadowsocks)
        """
        response = await InboundAPI.get_all_inbounds()
        if response and 'response' in response:
            inbounds = response['response']
            filtered_inbounds = [inbound for inbound in inbounds if inbound.get('protocol') == protocol]
            return {'response': filtered_inbounds}
        return response
    
    @staticmethod
    async def get_enabled_inbounds():
        """Get all enabled inbounds (client-side filtering)"""
        response = await InboundAPI.get_all_inbounds()
        if response and 'response' in response:
            inbounds = response['response']
            enabled_inbounds = [inbound for inbound in inbounds if not inbound.get('isDisabled', False)]
            return {'response': enabled_inbounds}
        return response
    
    @staticmethod
    async def get_disabled_inbounds():
        """Get all disabled inbounds (client-side filtering)"""
        response = await InboundAPI.get_all_inbounds()
        if response and 'response' in response:
            inbounds = response['response']
            disabled_inbounds = [inbound for inbound in inbounds if inbound.get('isDisabled', False)]
            return {'response': disabled_inbounds}
        return response
    
    @staticmethod
    async def search_inbounds_by_tag(query):
        """Search inbounds by tag (client-side filtering)"""
        response = await InboundAPI.get_all_inbounds()
        if response and 'response' in response:
            inbounds = response['response']
            matched_inbounds = [
                inbound for inbound in inbounds 
                if query.lower() in inbound.get('tag', '').lower()
            ]
            return {'response': matched_inbounds}
        return response
    
    @staticmethod
    async def get_inbounds_by_port_range(min_port, max_port):
        """Get inbounds within port range (client-side filtering)"""
        response = await InboundAPI.get_all_inbounds()
        if response and 'response' in response:
            inbounds = response['response']
            filtered_inbounds = [
                inbound for inbound in inbounds 
                if min_port <= inbound.get('port', 0) <= max_port
            ]
            return {'response': filtered_inbounds}
        return response
    
    # Валидация данных inbound
    @staticmethod
    def validate_inbound_data(data):
        """
        Validate inbound data before sending to API
        
        Returns:
            tuple: (is_valid, error_message)
        """
        required_fields = ['tag', 'protocol', 'port']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        
        # Validate port range
        port = data.get('port')
        if not isinstance(port, int) or port < 1 or port > 65535:
            return False, "Port must be between 1 and 65535"
        
        # Validate protocol
        valid_protocols = ['vless', 'vmess', 'trojan', 'shadowsocks']
        protocol = data.get('protocol')
        if protocol not in valid_protocols:
            return False, f"Protocol must be one of: {', '.join(valid_protocols)}"
        
        # Validate tag length (reasonable limit)
        tag = data.get('tag')
        if len(tag) > 100:
            return False, "Tag must be 100 characters or less"
        
        return True, None
    
    # Утилиты для создания inbound
    @staticmethod
    def create_inbound_template(tag, protocol, port, **kwargs):
        """
        Create an inbound data template with default values
        
        Args:
            tag: Inbound tag/name
            protocol: Protocol type
            port: Port number
            **kwargs: Additional optional parameters
        
        Returns:
            dict: Inbound data ready for API
        """
        inbound_data = {
            "tag": tag,
            "protocol": protocol,
            "port": port,
            "listen": kwargs.get("listen", "0.0.0.0")
        }
        
        # Add optional fields if provided
        optional_fields = ['settings', 'streamSettings', 'sniffing', 'allocate']
        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                inbound_data[field] = kwargs[field]
        
        return inbound_data
    
    # Утилиты для конкретных протоколов
    @staticmethod
    def create_vless_inbound(tag, port, **kwargs):
        """Create VLESS inbound template"""
        settings = kwargs.get('settings', {
            "clients": [],
            "decryption": "none",
            "fallbacks": []
        })
        
        return InboundAPI.create_inbound_template(
            tag=tag,
            protocol="vless",
            port=port,
            settings=settings,
            **kwargs
        )
    
    @staticmethod
    def create_vmess_inbound(tag, port, **kwargs):
        """Create VMess inbound template"""
        settings = kwargs.get('settings', {
            "clients": [],
            "default": {
                "level": 0,
                "alterId": 0
            }
        })
        
        return InboundAPI.create_inbound_template(
            tag=tag,
            protocol="vmess",
            port=port,
            settings=settings,
            **kwargs
        )
    
    @staticmethod
    def create_trojan_inbound(tag, port, **kwargs):
        """Create Trojan inbound template"""
        settings = kwargs.get('settings', {
            "clients": [],
            "fallbacks": []
        })
        
        return InboundAPI.create_inbound_template(
            tag=tag,
            protocol="trojan",
            port=port,
            settings=settings,
            **kwargs
        )
    
    @staticmethod
    def create_shadowsocks_inbound(tag, port, method="chacha20-poly1305", **kwargs):
        """Create Shadowsocks inbound template"""
        settings = kwargs.get('settings', {
            "method": method,
            "password": "",
            "network": "tcp,udp"
        })
        
        return InboundAPI.create_inbound_template(
            tag=tag,
            protocol="shadowsocks",
            port=port,
            settings=settings,
            **kwargs
        )