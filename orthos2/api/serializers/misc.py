from django.http import JsonResponse


class Serializer:

    @property
    def as_json(self):
        return JsonResponse(self.data)

    @property
    def data(self):
        return self._response


class SelectSerializer(Serializer):

    def __init__(self, queryset, title):
        self._response = {
            'header': {
                'type': 'SELECT',
                'title': title
            },
            'data': []
        }

        for item in queryset:
            self._response['data'].append(
                {
                    'value': str(item),
                    'url': '/{}/{}'.format(item.__class__.__name__.lower(), item.pk)
                }
            )


class MessageSerializer(Serializer):

    def __init__(self, message_type, message):
        self._response = {
            'header': {
                'type': 'MESSAGE'
            },
            'data': {
                'type': message_type,
                'message': str(message)
            }
        }


class Message(MessageSerializer):

    def __init__(self, message=''):
        super(Message, self).__init__(None, message)


class InfoMessage(MessageSerializer):

    def __init__(self, message=''):
        super(InfoMessage, self).__init__('INFO', message)


class WarningMessage(MessageSerializer):

    def __init__(self, message=''):
        super(WarningMessage, self).__init__('WARNING', message)


class ErrorMessage(MessageSerializer):

    def __init__(self, message=''):
        super(ErrorMessage, self).__init__('ERROR', message)


class RootSerializer(Serializer):

    def __init__(self, data):
        self._response = {
            'header': {
                'type': 'ROOT'
            },
            'data': data
        }


class AuthRequiredSerializer(Serializer):

    def __init__(self):
        self._response = {
            'header': {
                'type': 'AUTHREQUIRED'
            },
            'data': None
        }


class InputSerializer(Serializer):

    def __init__(self, data, target_url, order):
        self._response = {
            'header': {
                'type': 'INPUT',
                'target': target_url,
                'order': order
            },
            'data': data
        }
