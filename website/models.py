# models.py
from django.db import models
import uuid

class Visit(models.Model):
    slug = models.SlugField(unique=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    page_url = models.URLField()

    def __str__(self):
        return f"Visit to {self.page_url} at {self.created_at}"
class ContactMessage(models.Model):
    phone = models.CharField(max_length=15)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone
    
    def get_replies(self):
        # Return the related replies using the related name 'replies'
        return Reply.objects.filter(contact_message=self)  # Returns all replies associated with this contact message

class Reply(models.Model):
    contact_message = models.ForeignKey(ContactMessage, related_name='replies', on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply to {self.contact_message.phone}"
    
    