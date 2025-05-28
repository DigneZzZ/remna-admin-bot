from modules.api.client import RemnaAPI
import logging

logger = logging.getLogger(__name__)

class NodeAPI:
    """API methods for node management based on Remnawave API v1.6.5"""
    
    # Основные CRUD операции
    @staticmethod
    async def get_all_nodes():
        """Get all nodes"""
        return await RemnaAPI.get("nodes")
    
    @staticmethod
    async def get_node_by_uuid(uuid):
        """Get node by UUID"""
        return await RemnaAPI.get(f"nodes/{uuid}")
    
    @staticmethod
    async def create_node(data):
        """
        Create a new node
        
        Required fields:
        - name: Node name (string)
        - address: Node address (string)
        - port: Node port (integer, 1-65535)
        - usageCoefficient: Usage coefficient (number, default: 1.0)
        
        Optional fields:
        - countryCode: Country code (2-letter ISO code)
        - isDisabled: Node disabled status (default: false)
        """
        return await RemnaAPI.post("nodes", data)
    
    @staticmethod
    async def update_node(data):
        """
        Update a node
        
        Required field:
        - uuid: Node UUID
        
        Optional fields (same as create_node):
        - name, address, port, usageCoefficient, countryCode, isDisabled
        """
        return await RemnaAPI.patch("nodes", data)
    
    @staticmethod
    async def delete_node(uuid):
        """Delete a node by UUID"""
        return await RemnaAPI.delete(f"nodes/{uuid}")
    
    # Управление состоянием
    @staticmethod
    async def enable_node(uuid):
        """Enable a node"""
        return await RemnaAPI.post(f"nodes/{uuid}/enable")
    
    @staticmethod
    async def disable_node(uuid):
        """Disable a node"""
        return await RemnaAPI.post(f"nodes/{uuid}/disable")
    
    @staticmethod
    async def restart_node(uuid):
        """Restart a node"""
        return await RemnaAPI.post(f"nodes/{uuid}/restart")
    
    @staticmethod
    async def restart_all_nodes():
        """Restart all nodes"""
        return await RemnaAPI.post("nodes/actions/restart-all")
    
    # Операции с порядком
    @staticmethod
    async def reorder_nodes(nodes_data):
        """
        Reorder nodes
        
        Args:
            nodes_data: List of objects with 'uuid' and 'viewPosition' fields
            Example: [{"uuid": "node-uuid-1", "viewPosition": 1}, ...]
        """
        data = {"nodes": nodes_data}
        return await RemnaAPI.post("nodes/actions/reorder", data)
    
    # Массовые операции
    @staticmethod
    async def bulk_delete_nodes(uuids):
        """
        Delete multiple nodes by UUIDs
        
        Args:
            uuids: List of node UUIDs to delete
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("nodes/bulk/delete", data)
    
    @staticmethod
    async def bulk_enable_nodes(uuids):
        """
        Enable multiple nodes by UUIDs
        
        Args:
            uuids: List of node UUIDs to enable
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("nodes/bulk/enable", data)
    
    @staticmethod
    async def bulk_disable_nodes(uuids):
        """
        Disable multiple nodes by UUIDs
        
        Args:
            uuids: List of node UUIDs to disable
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("nodes/bulk/disable", data)
    
    @staticmethod
    async def bulk_restart_nodes(uuids):
        """
        Restart multiple nodes by UUIDs
        
        Args:
            uuids: List of node UUIDs to restart
        """
        data = {"uuids": uuids}
        return await RemnaAPI.post("nodes/bulk/restart", data)
    
    # Управление inbound'ами
    @staticmethod
    async def get_node_inbounds(uuid):
        """Get inbounds associated with node"""
        return await RemnaAPI.get(f"nodes/{uuid}/inbounds")
    
    @staticmethod
    async def add_inbound_to_node(node_uuid, inbound_uuid):
        """
        Add inbound to specific node
        
        Args:
            node_uuid: Node UUID
            inbound_uuid: Inbound UUID to add
        """
        data = {"inboundUuid": inbound_uuid}
        return await RemnaAPI.post(f"nodes/{node_uuid}/inbounds", data)
    
    @staticmethod
    async def remove_inbound_from_node(node_uuid, inbound_uuid):
        """
        Remove inbound from specific node
        
        Args:
            node_uuid: Node UUID
            inbound_uuid: Inbound UUID to remove
        """
        return await RemnaAPI.delete(f"nodes/{node_uuid}/inbounds/{inbound_uuid}")
    
    # Статистика и мониторинг
    @staticmethod
    async def get_node_usage_by_range(uuid, start_date, end_date):
        """
        Get node usage by date range
        
        Args:
            uuid: Node UUID
            start_date: Start date in ISO format
            end_date: End date in ISO format
        """
        params = {
            "start": start_date,
            "end": end_date
        }
        return await RemnaAPI.get(f"nodes/usage/{uuid}/users/range", params)
    
    @staticmethod
    async def get_nodes_usage_by_range(start_date, end_date):
        """
        Get all nodes usage by date range
        
        Args:
            start_date: Start date in ISO format
            end_date: End date in ISO format
        """
        params = {
            "start": start_date,
            "end": end_date
        }
        return await RemnaAPI.get("nodes/usage/range", params)
    
    @staticmethod
    async def get_nodes_realtime_usage():
        """
        Get nodes realtime usage
        
        Returns real-time usage statistics for all nodes
        """
        logger.info("Requesting nodes realtime usage from API")
        
        try:
            result = await RemnaAPI.get("nodes/usage/realtime")
            logger.info(f"Nodes realtime usage API response received")
            
            # If empty result, create fallback data from nodes info
            if not result or (isinstance(result, dict) and result.get('response') == []):
                logger.info("Realtime usage empty, creating fallback data")
                return await NodeAPI._create_fallback_usage_data()
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting realtime usage: {e}")
            return await NodeAPI._create_fallback_usage_data()
    
    @staticmethod
    async def _create_fallback_usage_data():
        """Create fallback usage data from nodes info"""
        try:
            nodes_response = await NodeAPI.get_all_nodes()
            if not nodes_response or 'response' not in nodes_response:
                return {'response': []}
            
            nodes = nodes_response['response']
            usage_data = []
            
            for node in nodes:
                usage_data.append({
                    'nodeUuid': node.get('uuid'),
                    'nodeName': node.get('name', 'Unknown'),
                    'countryCode': node.get('countryCode', 'XX'),
                    'downloadBytes': 0,
                    'uploadBytes': 0,
                    'totalBytes': 0,
                    'downloadSpeedBps': 0,
                    'uploadSpeedBps': 0,
                    'totalSpeedBps': 0,
                    'isConnected': node.get('isConnected', False),
                    'status': 'connected' if node.get('isConnected', False) else 'disconnected'
                })
            
            logger.info(f"Created fallback usage data for {len(usage_data)} nodes")
            return {'response': usage_data}
            
        except Exception as e:
            logger.error(f"Error creating fallback usage data: {e}")
            return {'response': []}
    
    # Сертификаты и ключи
    @staticmethod
    async def get_node_certificate():
        """Get panel public key for node certificate"""
        return await RemnaAPI.get("keygen")
    
    # Дополнительные утилитарные методы (клиентская фильтрация)
    @staticmethod
    async def get_enabled_nodes():
        """Get all enabled nodes (client-side filtering)"""
        response = await NodeAPI.get_all_nodes()
        if response and 'response' in response:
            nodes = response['response']
            enabled_nodes = [node for node in nodes if not node.get('isDisabled', False)]
            return {'response': enabled_nodes}
        return response
    
    @staticmethod
    async def get_disabled_nodes():
        """Get all disabled nodes (client-side filtering)"""
        response = await NodeAPI.get_all_nodes()
        if response and 'response' in response:
            nodes = response['response']
            disabled_nodes = [node for node in nodes if node.get('isDisabled', False)]
            return {'response': disabled_nodes}
        return response
    
    @staticmethod
    async def get_connected_nodes():
        """Get connected nodes (client-side filtering)"""
        response = await NodeAPI.get_all_nodes()
        if response and 'response' in response:
            nodes = response['response']
            connected_nodes = [node for node in nodes if node.get('isConnected', False)]
            return {'response': connected_nodes}
        return response
    
    @staticmethod
    async def get_disconnected_nodes():
        """Get disconnected nodes (client-side filtering)"""
        response = await NodeAPI.get_all_nodes()
        if response and 'response' in response:
            nodes = response['response']
            disconnected_nodes = [node for node in nodes if not node.get('isConnected', False)]
            return {'response': disconnected_nodes}
        return response
    
    @staticmethod
    async def search_nodes_by_name(query):
        """Search nodes by name (client-side filtering)"""
        response = await NodeAPI.get_all_nodes()
        if response and 'response' in response:
            nodes = response['response']
            matched_nodes = [
                node for node in nodes 
                if query.lower() in node.get('name', '').lower()
            ]
            return {'response': matched_nodes}
        return response
    
    @staticmethod
    async def get_nodes_by_country(country_code):
        """Get nodes by country code (client-side filtering)"""
        response = await NodeAPI.get_all_nodes()
        if response and 'response' in response:
            nodes = response['response']
            country_nodes = [
                node for node in nodes 
                if node.get('countryCode', '').upper() == country_code.upper()
            ]
            return {'response': country_nodes}
        return response
    
    # Валидация данных node
    @staticmethod
    def validate_node_data(data):
        """
        Validate node data before sending to API
        
        Returns:
            tuple: (is_valid, error_message)
        """
        required_fields = ['name', 'address', 'port']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        
        # Validate port range
        port = data.get('port')
        if not isinstance(port, int) or port < 1 or port > 65535:
            return False, "Port must be between 1 and 65535"
        
        # Validate usage coefficient
        usage_coef = data.get('usageCoefficient')
        if usage_coef is not None:
            if not isinstance(usage_coef, (int, float)) or usage_coef <= 0:
                return False, "Usage coefficient must be a positive number"
        
        # Validate country code if provided
        country_code = data.get('countryCode')
        if country_code and len(country_code) != 2:
            return False, "Country code must be a 2-letter ISO code"
        
        # Validate name length
        name = data.get('name', '')
        if len(name) > 100:
            return False, "Name must be 100 characters or less"
        
        return True, None
    
    # Утилиты для создания nodes
    @staticmethod
    def create_node_template(name, address, port, **kwargs):
        """
        Create a node data template with default values
        
        Args:
            name: Node name
            address: Node address
            port: Node port
            **kwargs: Additional optional parameters
        
        Returns:
            dict: Node data ready for API
        """
        node_data = {
            "name": name,
            "address": address,
            "port": port,
            "usageCoefficient": kwargs.get("usageCoefficient", 1.0),
            "isDisabled": kwargs.get("isDisabled", False)
        }
        
        # Add optional fields if provided
        optional_fields = ['countryCode']
        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                node_data[field] = kwargs[field]
        
        return node_data
    
    # Вспомогательные методы для одиночных операций
    @staticmethod
    async def enable_single_node(uuid):
        """Enable a single node using bulk operation"""
        return await NodeAPI.bulk_enable_nodes([uuid])
    
    @staticmethod
    async def disable_single_node(uuid):
        """Disable a single node using bulk operation"""
        return await NodeAPI.bulk_disable_nodes([uuid])
    
    @staticmethod
    async def restart_single_node(uuid):
        """Restart a single node using bulk operation"""
        return await NodeAPI.bulk_restart_nodes([uuid])
    
    # Статистика для совместимости
    @staticmethod
    async def get_nodes_stats():
        """
        Get nodes statistics (compatibility method)
        Transform nodes data to stats format for existing code
        """
        try:
            logger.info("Requesting nodes stats from API")
            
            response = await NodeAPI.get_all_nodes()
            if not response or 'response' not in response:
                logger.warning("No nodes data returned")
                return []
            
            nodes = response['response']
            stats_data = []
            
            for node in nodes:
                stats_data.append({
                    'name': node.get('name', 'Unknown'),
                    'status': 'connected' if node.get('isConnected', False) else 'disconnected',
                    'uptime': node.get('uptime', 'N/A'),
                    'id': node.get('id', node.get('uuid')),
                    'uuid': node.get('uuid'),
                    'address': node.get('address', 'Unknown'),
                    'port': node.get('port'),
                    'usage_coefficient': node.get('usageCoefficient', 1.0),
                    'version': node.get('version', 'Unknown'),
                    'last_connected_at': node.get('lastConnectedAt'),
                    'country_code': node.get('countryCode'),
                    'is_disabled': node.get('isDisabled', False),
                    'is_connected': node.get('isConnected', False)
                })
                
            logger.info(f"Processed {len(stats_data)} nodes for stats")
            return stats_data
            
        except Exception as e:
            logger.error(f"Error getting nodes stats: {e}", exc_info=True)
            return []