from abc import ABC, abstractmethod

class BaseVCSClient(ABC):
    """
    Base VCS client
    """
    api_key: str # Client API key

    @abstractmethod
    def verify_connection(self) -> bool:
        """Test if the API key and connection are valid"""
        pass
    
    @abstractmethod
    def get_diff(self, **kwargs) -> str:
        """
        Get diff of a pull request
        """
        pass

    @abstractmethod
    def post_comment(self, **kwargs) -> dict:
        """
        Post comment to a pull request
        """
        pass