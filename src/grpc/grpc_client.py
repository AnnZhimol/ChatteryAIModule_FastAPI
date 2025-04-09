import grpc
import src.generate.twitch_pb2_grpc as twitch_pb2__grpc
import src.generate.twitch_pb2 as twitch__pb2


class GRPCClient:
    def __init__(self, host="localhost", port=9090):
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = twitch_pb2__grpc.MessageServiceStub(self.channel)

    def send_message(self, user, message, sentence_type, sentiment_type, parent_user, parent_message, channel,
                     timestamp, trans_id):
        request = twitch__pb2.TwitchMessage(
            user=user,
            message=message,
            sentence_type=sentence_type,
            sentiment_type=sentiment_type,
            parent_user=parent_user if parent_user else "",
            parent_message=parent_message if parent_message else "",
            channel=channel,
            timestamp=timestamp,
            trans_id=trans_id
        )
        return self.stub.SendMessage(request)
