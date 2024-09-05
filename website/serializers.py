# serializers.py
from rest_framework import serializers
from .models import ContactMessage, Reply, Visit

class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = ['slug', 'page_url', 'created_at']



class ReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Reply
        fields = ['id', 'contact_message', 'message', 'created_at']


class ContactMessageSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField(read_only=True)
    last_reply = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ContactMessage
        fields = ['id', 'phone', 'message', 'created_at', 'replies', 'last_reply']

    def get_replies(self, obj):
        return ReplySerializer(obj.get_replies(), many=True).data

    def get_last_reply(self, obj):
        replies = obj.get_replies()
        if replies:
            return ReplySerializer(replies.last()).data
        return None
    
