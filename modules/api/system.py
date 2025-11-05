from modules.api.client import RemnaAPI

class SystemAPI:
    """API methods for system management"""
    
    @staticmethod
    async def get_stats():
        """Get system statistics"""
        return await RemnaAPI.get("system/stats")
    
    @staticmethod
    async def get_bandwidth_stats():
        """Get bandwidth statistics"""
        return await RemnaAPI.get("system/stats/bandwidth")
    
    @staticmethod
    async def get_nodes_statistics():
        """Get nodes statistics"""
        return await RemnaAPI.get("system/stats/nodes")

    
    @staticmethod
    async def get_xray_config():
        """Not available in v208"""
        return None
    
    @staticmethod
    async def update_xray_config(config_data):
        """Not available in v208"""
        return None
