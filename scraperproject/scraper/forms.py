from django import forms

class ScrapeForm(forms.Form):
    search_query = forms.CharField(label='Search Query', max_length=100)
    location = forms.CharField(label='Location', max_length=100)
    num_pages = forms.IntegerField(label='Number of Pages', min_value=1)
