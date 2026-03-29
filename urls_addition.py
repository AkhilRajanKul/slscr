# Add these two lines to your urlpatterns list in urls.py:

path('script-generator/', views.script_generator, name='script_generator'),
path('generate-script/',  views.generate_script,  name='generate_script'),
