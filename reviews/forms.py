# reviews/forms.py
from django import forms
from .models import Review

# reviews/forms.py
from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        required=True,
        widget=forms.Select(
            choices=[('', 'Select Rating')] + [(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(5, 0, -1)],
            attrs={'class': 'form-select'}
        )
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Share your experience learning this course...'
            }),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None or rating < 1 or rating > 5:
            raise forms.ValidationError("Please provide a valid rating between 1 and 5 stars.")
        return rating

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        if not comment:
            raise forms.ValidationError("Your review comment cannot be empty.")
        if len(comment) < 10:
            raise forms.ValidationError("Please share a bit more detail. Your comment must be at least 10 characters long.")
        return comment