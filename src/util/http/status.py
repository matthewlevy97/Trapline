
class HTTPStatus:
    _messages = {
        100: 'Continue',
        101: 'Switching Protocols',

        200: 'OK',
        201: 'Created',
        202: 'Accepted',
        204: 'No Content',

        301: 'Moved Permanently',
        302: 'Found',
        305: 'Use Proxy',
        307: 'Temporary Redirect',
        308: 'Permanent Redirect',

        400: 'Bad Request',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed',
        406: 'Not Acceptable',
        408: 'Request Timeout',
        410: 'Gone',
        411: 'Length Required',
        414: 'Request-URI Too Long',
        429: 'Too Many Requests',

        500: 'Internal Server Error',
        501: 'Not Implemented',
        502: 'Bad Gateway',
        503: 'Service Unavailable',
        505: 'HTTP Version Not Supported'
    }

    @staticmethod
    def message(code: int) -> str:
        if code in HTTPStatus._messages:
            return HTTPStatus._messages[code]
        return ''
    
    CONTINUE = 100
    SWITCHING_PROTOCOLS = 101
    
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204

    MOVED_PERMANENTLY = 301
    FOUND = 302
    USE_PROXY = 305
    TEMPORARY_REDIRECT = 307
    PERMANENT_REDIRECT = 308

    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    REQUEST_TIMEOUT = 408
    GONE = 410
    LENGTH_REQUIRED = 411
    REQUEST_URI_TOO_LONG = 414
    TOO_MANY_REQUESTS = 429

    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    HTTP_VERSION_NOT_SUPPORTED = 505