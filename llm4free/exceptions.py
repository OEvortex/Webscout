WATCH_URL = 'https://www.youtube.com/watch?v={video_id}'


class WebscoutE(Exception):
    """
    Base exception class for all Webscout related errors.

    This class serves as the root for all custom exceptions raised by the Webscout library.
    It provides a common base for catching and handling errors specific to Webscout.
    """
    pass


class ModelNotFoundError(WebscoutE):
    """
    Exception raised when a requested model is not found or available.

    This exception is raised when the specified model cannot be located or accessed by the provider.
    It indicates that the model name might be incorrect or the provider does not support it.
    """
    pass


class MissingRequirementsError(WebscoutE):
    """
    Exception raised when required dependencies are missing.

    This exception is raised when a feature requires certain libraries or packages that are not installed.
    It indicates that the user needs to install the missing dependencies to use the feature.
    """
    pass


class APIConnectionError(WebscoutE):
    """
    Exception raised when there are issues connecting to an API.

    This exception is raised when a network connection to an external API fails.
    It indicates a problem with the network or the API server itself.
    """
    pass


class AuthenticationError(WebscoutE):
    """
    Exception raised when authentication to a service fails.

    This exception is raised when the provided credentials are invalid or expired.
    It indicates that the application cannot authenticate with the service.
    """
    pass


class RatelimitE(WebscoutE):
    """
    Exception raised when an API rate limit is exceeded.

    This exception is raised when the number of requests to an API exceeds the allowed limit within a given time frame.
    It indicates that the application is making too many requests and needs to slow down.
    """
    pass


class ConversationLimitException(WebscoutE):
    """
    Exception raised when a conversation limit is exceeded.

    This exception is raised when a limit on the number of turns or messages in a conversation is exceeded.
    It indicates that the conversation has reached its maximum allowed length.
    """
    pass


class TimeoutE(WebscoutE):
    """
    Exception raised when a request to an API times out.

    This exception is raised when a request to an API takes longer than the allowed time to complete.
    It indicates a problem with the network or the API server being slow to respond.
    """
    pass


class FailedToGenerateResponseError(WebscoutE):
    """
    Exception raised when a provider fails to generate a response.

    This exception is raised when a provider is unable to generate a response for a given request.
    It indicates an issue with the provider's logic or data.
    """
    pass

class InvalidResponseError(WebscoutE):
    """
    Exception raised when an API response is invalid or unexpected.

    This exception is raised when the response from an API does not match the expected format or contains invalid data.
    It indicates an issue with the API response parsing or structure.
    """
    pass

class ProviderConnectionError(WebscoutE):
    """
    Exception raised when there are issues connecting to a specific provider.
    """
    pass

class InvalidOptimizerError(WebscoutE):
    """
    Exception raised when an invalid or unavailable optimizer is requested.
    """
    pass

class InvalidAuthenticationError(Exception):
    """Custom exception for authentication errors (e.g., invalid API key, cookies)."""
    pass

class AllProvidersFailure(WebscoutE):
    """
    Exception raised when all providers fail to generate a response.

    This exception is raised when none of the available providers are able to generate a response for a given request.
    It indicates a widespread issue with all providers.
    """
    pass


class FacebookInvalidCredentialsException(WebscoutE):
    """
    Exception raised when Facebook credentials are invalid.

    This exception is raised when the provided Facebook credentials (e.g., username, password, cookies) are invalid.
    It indicates that the application is unable to authenticate with Facebook.
    """
    pass


class FacebookRegionBlocked(WebscoutE):
    """
    Exception raised when Facebook access is blocked due to region restrictions.

    This exception is raised when access to Facebook is blocked due to geographical restrictions.
    It indicates that the application is unable to access Facebook from the current location.
    """
    pass


class ModelUnloadedException(WebscoutE):
    """
    Exception raised when a model is unloaded.

    This exception is raised when a required model is not loaded or has been unloaded.
    It indicates that the application is unable to perform operations that require the model.
    """
    pass


class TranscriptRetrievalError(WebscoutE):
    """
    Base class for transcript retrieval errors.

    This class serves as the root for all custom exceptions related to transcript retrieval.
    It provides a common base for catching and handling errors specific to transcript retrieval.

    Args:
        video_id (str): The ID of the video for which the transcript retrieval failed.
        message (str): A message describing the error.
    """

    def __init__(self, video_id, message):
        super().__init__(message.format(video_url=WATCH_URL.format(video_id=video_id)))
        self.video_id = video_id


class YouTubeRequestFailedError(TranscriptRetrievalError):
    """
    Exception raised when a request to YouTube fails.

    This exception is raised when a network request to YouTube fails.
    It indicates a problem with the network or the YouTube server itself.

    Args:
        video_id (str): The ID of the video for which the request failed.
        http_error (str): The HTTP error that occurred.
    """

    def __init__(self, video_id, http_error):
        message = 'Request to YouTube failed: {reason}'
        super().__init__(video_id, message.format(reason=str(http_error)))


class VideoUnavailableError(TranscriptRetrievalError):
    """
    Exception raised when the video is unavailable.

    This exception is raised when the requested video is no longer available on YouTube.
    It indicates that the video has been removed or made private.

    Args:
        video_id (str): The ID of the unavailable video.
    """

    def __init__(self, video_id):
        message = 'The video is no longer available'
        super().__init__(video_id, message)


class InvalidVideoIdError(TranscriptRetrievalError):
    """
    Exception raised when an invalid video ID is provided.

    This exception is raised when the provided video ID is not in the correct format.
    It indicates that the application is using a URL instead of the video ID.

    Args:
        video_id (str): The invalid video ID.
    """

    def __init__(self, video_id):
        message = (
            'You provided an invalid video id. Make sure you are using the video id and NOT the url!\n\n'
            'Do NOT run: `YTTranscriber.get_transcript("https://www.youtube.com/watch?v=1234")`\n'
            'Instead run: `YTTranscriber.get_transcript("1234")`'
        )
        super().__init__(video_id, message)


class TooManyRequestsError(TranscriptRetrievalError):
    """
    Exception raised when YouTube rate limits the requests.

    This exception is raised when YouTube rate limits the requests from the current IP address.
    It indicates that the application is making too many requests and needs to slow down or use a different IP.

    Args:
        video_id (str): The ID of the video for which the request was rate-limited.
    """

    def __init__(self, video_id):
        message = (
            'YouTube is receiving too many requests from this IP and now requires solving a captcha to continue. '
            'One of the following things can be done to work around this:\n\
            - Manually solve the captcha in a browser and export the cookie. '
            '- Use a different IP address\n\
            - Wait until the ban on your IP has been lifted'
        )
        super().__init__(video_id, message)


class TranscriptsDisabledError(TranscriptRetrievalError):
    """
    Exception raised when transcripts are disabled for the video.

    This exception is raised when the video has subtitles disabled.
    It indicates that the application cannot retrieve transcripts for this video.

    Args:
        video_id (str): The ID of the video with disabled transcripts.
    """

    def __init__(self, video_id):
        message = 'Subtitles are disabled for this video'
        super().__init__(video_id, message)


class NoTranscriptAvailableError(TranscriptRetrievalError):
    """
    Exception raised when no transcripts are available for the video.

    This exception is raised when the video has no transcripts available.
    It indicates that the application cannot retrieve transcripts for this video.

    Args:
        video_id (str): The ID of the video with no available transcripts.
    """

    def __init__(self, video_id):
        message = 'No transcripts are available for this video'
        super().__init__(video_id, message)


class NotTranslatableError(TranscriptRetrievalError):
    """
    Exception raised when the transcript is not translatable.

    This exception is raised when the requested language is not translatable.
    It indicates that the application cannot translate the transcript to the requested language.

    Args:
        video_id (str): The ID of the video with a non-translatable transcript.
    """

    def __init__(self, video_id):
        message = 'The requested language is not translatable'
        super().__init__(video_id, message)


class TranslationLanguageNotAvailableError(TranscriptRetrievalError):
    """
    Exception raised when the requested translation language is not available.

    This exception is raised when the requested translation language is not supported for the transcript.
    It indicates that the application cannot translate the transcript to the requested language.

    Args:
        video_id (str): The ID of the video for which the translation language is not available.
    """

    def __init__(self, video_id):
        message = 'The requested translation language is not available'
        super().__init__(video_id, message)


class CookiePathInvalidError(TranscriptRetrievalError):
    """
    Exception raised when the cookie path is invalid.

    This exception is raised when the provided cookie path is invalid.
    It indicates that the application cannot access the cookie file.

    Args:
        video_id (str): The ID of the video for which the cookie path is invalid.
    """

    def __init__(self, video_id):
        message = 'The provided cookie path is invalid'
        super().__init__(video_id, message)


class CookiesInvalidError(TranscriptRetrievalError):
    """
    Exception raised when the provided cookies are invalid.

    This exception is raised when the provided cookies are not valid or have expired.
    It indicates that the application cannot authenticate with YouTube using the provided cookies.

    Args:
        video_id (str): The ID of the video for which the cookies are invalid.
    """

    def __init__(self, video_id):
        message = 'The cookies provided are not valid (may have expired)'
        super().__init__(video_id, message)


class FailedToCreateConsentCookieError(TranscriptRetrievalError):
    """
    Exception raised when consent cookie creation fails.

    This exception is raised when the application fails to automatically give consent to saving cookies.
    It indicates that the application cannot proceed without the consent cookie.

    Args:
        video_id (str): The ID of the video for which the consent cookie creation failed.
    """

    def __init__(self, video_id):
        message = 'Failed to automatically give consent to saving cookies'
        super().__init__(video_id, message)


class NoTranscriptFoundError(TranscriptRetrievalError):
    """
    Exception raised when no transcript is found for the requested language codes.

    This exception is raised when no transcripts are found for any of the requested language codes.
    It indicates that the application cannot retrieve transcripts for the requested languages.

    Args:
        video_id (str): The ID of the video for which no transcript was found.
        requested_language_codes (list): The list of requested language codes.
        transcript_data (dict): The transcript data that was found.
    """

    def __init__(self, video_id, requested_language_codes, transcript_data):
        message = (
            'No transcripts were found for any of the requested language codes: {requested_language_codes}\n\n'
            '{transcript_data}'
        )
        super().__init__(video_id, message.format(
            requested_language_codes=requested_language_codes,
            transcript_data=str(transcript_data)
        ))
