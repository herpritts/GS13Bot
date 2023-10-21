"""
This module defines custom exceptions used in the job posting process.

Classes:
    JobPostingError: Exception for errors in the job posting process.
    NetworkError: Exception for network errors.
"""

class JobPostingError(Exception):
    """
    Exception raised for errors in the job posting process.

    Attributes:
        message (str): explanation of the error
    """

    def __init__(self, message="An error occurred while checking for job posting"):
        """
        Constructs all the necessary attributes for the JobPostingError object.

        Args:
            message (str): explanation of the error
        """
        self.message = message
        super().__init__(self.message)


class NetworkError(Exception):
    """
    Exception raised for network errors.

    Attributes:
        message (str): explanation of the error
    """

    def __init__(self, message="A network error occurred while checking for job posting"):
        """
        Constructs all the necessary attributes for the NetworkError object.

        Args:
            message (str): explanation of the error
        """
        self.message = message
        super().__init__(self.message)
