from modules.api.client import RemnaAPI

class HostAPI:
    """API methods for host management based on Remnawave API v1.6.5"""
    
    # Основные CRUD операции
    @staticmethod
    async def get_all_hosts():
        """Get all hosts"""
        return await RemnaAPI.get("hosts")
    
    @staticmethod
    async def get_host_by_uuid(uuid):
        """Get host by UUID"""
        return await RemnaAPI.get(f"hosts/{uuid}")
    
    @staticmethod
    async def create_host(data):
        """
        Create a new host
        
        Required fields:
        - inboundUuid: UUID of the inbound (format: uuid)
        - remark: Host description (max 40 chars)
        - address: Host address
        - port: Port number (integer)
        
        Optional fields:
        - path: Path for the host
        - sni: Server Name Indication
        - host: Host header
        - alpn: ALPN setting (h3, h2, http/1.1, h2,http/1.1, h3,h2,http/1.1, h3,h2)
        - fingerprint: TLS fingerprint (chrome, firefox, safari, ios, android, edge, qq, random, randomized)
        - allowInsecure: Allow insecure connections (default: false)
        - isDisabled: Host disabled status (default: false)
        - securityLayer: Security layer (DEFAULT, TLS, NONE - default: DEFAULT)
        - xHttpExtraParams: Extra parameters for HTTP
        """
        return await RemnaAPI.post("hosts", data)
    
    @staticmethod
    async def update_host(data):
        """
        Update a host
        
        Required field:
        - uuid: Host UUID
        
        Optional fields (same as create_host):
        - inboundUuid, remark, address, port, path, sni, host, alpn, 
          fingerprint, allowInsecure, isDisabled, securityLayer, xHttpExtraParams
        """
        return await RemnaAPI.patch("hosts", data)
    
    @staticmethod
    async def delete_host(uuid):
        """Delete a host by UUID"""
        return await RemnaAPI.delete(f"hosts/{uuid}")
    
    # Операции с порядком
    @staticmethod
    async def reorder_hosts(hosts_data):
        """
        Reorder hosts
        
        Args:
            hosts_data: List of objects with 'uuid' and 'viewPosition' fields
            Example: [{"uuid": "host-uuid-1", "viewPosition": 1}, ...]
        """
        data = {"hosts": hosts_data}
        return await RemnaAPI.post("hosts/actions/reorder", data)
    
    # Массовые операции
    @staticmethod
    async def bulk_delete_hosts(uuids):
        """
        Delete multiple hosts by UUIDs
        
        Args:
            uuids: List of host UUIDs to delete
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("hosts/bulk/delete", data)
    
    @staticmethod
    async def bulk_enable_hosts(uuids):
        """
        Enable multiple hosts by UUIDs
        
        Args:
            uuids: List of host UUIDs to enable
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("hosts/bulk/enable", data)
    
    @staticmethod
    async def bulk_disable_hosts(uuids):
        """
        Disable multiple hosts by UUIDs
        
        Args:
            uuids: List of host UUIDs to disable
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("hosts/bulk/disable", data)
    
    @staticmethod
    async def bulk_set_inbound_to_hosts(uuids, inbound_uuid):
        """
        Set inbound to multiple hosts by UUIDs
        
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
    async def bulk_set_port_to_hosts(uuids, port):
        """
        Set port to multiple hosts by UUIDs
        
        Args:
            uuids: List of host UUIDs
            port: Port number (1-65535)
        """
        data = {
            "uuids": uuids,
            "port": port
        }
        return await RemnaAPI.post("hosts/bulk/set-port", data)
    
    # Вспомогательные методы для работы с состоянием отдельных хостов
    @staticmethod
    async def enable_host(uuid):
        """Enable a single host using bulk operation"""
        return await HostAPI.bulk_enable_hosts([uuid])
    
    @staticmethod
    async def disable_host(uuid):
        """Disable a single host using bulk operation"""
        return await HostAPI.bulk_disable_hosts([uuid])
    
    @staticmethod
    async def set_host_inbound(uuid, inbound_uuid):
        """Set inbound for a single host using bulk operation"""
        return await HostAPI.bulk_set_inbound_to_hosts([uuid], inbound_uuid)
    
    @staticmethod
    async def set_host_port(uuid, port):
        """Set port for a single host using bulk operation"""
        return await HostAPI.bulk_set_port_to_hosts([uuid], port)
    
    # Дополнительные утилитарные методы (клиентская фильтрация)
    @staticmethod
    async def get_hosts_by_inbound(inbound_uuid):
        """
        Get all hosts and filter by inbound UUID (client-side filtering)
        """
        response = await HostAPI.get_all_hosts()
        if response and 'response' in response:
            hosts = response['response']
            filtered_hosts = [host for host in hosts if host.get('inboundUuid') == inbound_uuid]
            return {'response': filtered_hosts}
        return response
    
    @staticmethod
    async def get_enabled_hosts():
        """Get all enabled hosts (client-side filtering)"""
        response = await HostAPI.get_all_hosts()
        if response and 'response' in response:
            hosts = response['response']
            enabled_hosts = [host for host in hosts if not host.get('isDisabled', False)]
            return {'response': enabled_hosts}
        return response
    
    @staticmethod
    async def get_disabled_hosts():
        """Get all disabled hosts (client-side filtering)"""
        response = await HostAPI.get_all_hosts()
        if response and 'response' in response:
            hosts = response['response']
            disabled_hosts = [host for host in hosts if host.get('isDisabled', False)]
            return {'response': disabled_hosts}
        return response
    
    @staticmethod
    async def search_hosts_by_remark(query):
        """Search hosts by remark (client-side filtering)"""
        response = await HostAPI.get_all_hosts()
        if response and 'response' in response:
            hosts = response['response']
            matched_hosts = [
                host for host in hosts 
                if query.lower() in host.get('remark', '').lower()
            ]
            return {'response': matched_hosts}
        return response
    
    @staticmethod
    async def search_hosts_by_address(query):
        """Search hosts by address (client-side filtering)"""
        response = await HostAPI.get_all_hosts()
        if response and 'response' in response:
            hosts = response['response']
            matched_hosts = [
                host for host in hosts 
                if query.lower() in host.get('address', '').lower()
            ]
            return {'response': matched_hosts}
        return response
    
    # Валидация данных хоста
    @staticmethod
    def validate_host_data(data):
        """
        Validate host data before sending to API
        
        Returns:
            tuple: (is_valid, error_message)
        """
        required_fields = ['inboundUuid', 'remark', 'address', 'port']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        
        # Validate remark length
        if len(data['remark']) > 40:
            return False, "Remark must be 40 characters or less"
        
        # Validate port range
        port = data.get('port')
        if not isinstance(port, int) or port < 1 or port > 65535:
            return False, "Port must be between 1 and 65535"
        
        # Validate security layer if provided
        valid_security_layers = ['DEFAULT', 'TLS', 'NONE']
        security_layer = data.get('securityLayer')
        if security_layer and security_layer not in valid_security_layers:
            return False, f"Security layer must be one of: {', '.join(valid_security_layers)}"
        
        # Validate ALPN if provided
        valid_alpn = ['h3', 'h2', 'http/1.1', 'h2,http/1.1', 'h3,h2,http/1.1', 'h3,h2']
        alpn = data.get('alpn')
        if alpn and alpn not in valid_alpn:
            return False, f"ALPN must be one of: {', '.join(valid_alpn)}"
        
        # Validate fingerprint if provided
        valid_fingerprints = ['chrome', 'firefox', 'safari', 'ios', 'android', 'edge', 'qq', 'random', 'randomized']
        fingerprint = data.get('fingerprint')
        if fingerprint and fingerprint not in valid_fingerprints:
            return False, f"Fingerprint must be one of: {', '.join(valid_fingerprints)}"
        
        return True, None
    
    # Утилиты для создания хостов
    @staticmethod
    def create_host_template(inbound_uuid, remark, address, port, **kwargs):
        """
        Create a host data template with default values
        
        Args:
            inbound_uuid: UUID of the inbound
            remark: Host description
            address: Host address
            port: Port number
            **kwargs: Additional optional parameters
        
        Returns:
            dict: Host data ready for API
        """
        host_data = {
            "inboundUuid": inbound_uuid,
            "remark": remark,
            "address": address,
            "port": port,
            "allowInsecure": kwargs.get("allowInsecure", False),
            "isDisabled": kwargs.get("isDisabled", False),
            "securityLayer": kwargs.get("securityLayer", "DEFAULT")
        }
        
        # Add optional fields if provided
        optional_fields = ['path', 'sni', 'host', 'alpn', 'fingerprint', 'xHttpExtraParams']
        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                host_data[field] = kwargs[field]
        
        return host_data