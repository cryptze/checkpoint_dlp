from django.db import models

class Pattern(models.Model):
    name = models.CharField(max_length=255)
    regex = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class DetectedLeak(models.Model):
    pattern = models.ForeignKey(Pattern, on_delete=models.CASCADE)
    message_content = models.TextField()
    channel = models.CharField(max_length=255)
    author = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"Leak detected in {self.channel} by {self.author} at {self.timestamp}"