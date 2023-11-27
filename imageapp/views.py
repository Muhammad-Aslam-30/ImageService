from rest_framework import viewsets
from rest_framework import serializers
from .models import Images
from .serializer import ImageSerializer, RegisterSerializer, LoginSerializer
from rest_framework.response import Response
from rest_framework import status
import requests
import os
import hashlib
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from requests.exceptions import RequestException
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.exceptions import APIException
from django.db import models

class LoginAPI(APIView):
    def post(self, request):
        try:
            # Extract data from the request
            data = request.data
                
            # Create a serializer instance for login data
            serializer = LoginSerializer(data=data)
                
            # Check if the serializer is valid
            serializer.is_valid(raise_exception=True)

            # Authenticate user with provided credentials
            user = authenticate(username=serializer.data['username'], password=serializer.data['password'])

            # If authentication fails, raise an exception
            if not user:
                raise ValueError('Invalid credentials')

            # Get or create a token for the authenticated user
            token, _ = Token.objects.get_or_create(user=user)

            # Return a success response with the generated token
            return Response({
                'status': True,
                'message': 'User login successful',
                'token': str(token)
            }, status.HTTP_201_CREATED)

        except ValueError as ve:
            # Handle authentication failure
            return Response({
                'status': False,
                'message': str(ve)
            }, status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Handle unexpected errors
            return Response({
                'status': False,
                'message': 'An unexpected error occurred during login'
            }, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class RegisterAPI(APIView):

    def post(self, request):
        try:
            # Extract data from the request
            data = request.data

            # Create a serializer instance for registration data
            serializer = RegisterSerializer(data=data)

            # Check if the serializer is valid
            serializer.is_valid(raise_exception=True)

            # Save the user using the serializer
            serializer.save()

            # Return a success response
            return Response({
                'status': True,
                'message': 'User created successfully'
            }, status.HTTP_201_CREATED)

        except serializers.ValidationError as ve:
            # Handle validation errors (e.g., unique constraint violation)
            return Response({
                'status': False,
                'message': str(ve)
            }, status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Handle unexpected errors
            return Response({
                'status': False,
                'message': 'An unexpected error occurred during user registration'
            }, status.HTTP_500_INTERNAL_SERVER_ERROR)

class ImageViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = Images.objects.all()
    serializer_class = ImageSerializer
    lookup_field = 'url'

    def create(self, request, *args, **kwargs):

        # Get the list of image URLs from the request data
        image_urls = request.data.get('image_urls', [])

        # Ensure the media directory exists
        media_directory = os.path.join("media")
        os.makedirs(media_directory, exist_ok=True)

        # Process each image URL in the list
        for url in image_urls:
            # Check if the URL is already in the database
            if not Images.objects.filter(url=url).exists():
                try:
                    # Make an HTTP request to get the image content
                    response = requests.get(url)
                    response.raise_for_status()

                    # Generate a unique hash for the image URL
                    image_hash = hashlib.sha256(url.encode()).hexdigest()
                    imagename = f"image-{image_hash}.jpeg"
                    image_path = os.path.join(media_directory, imagename)

                    # Save the image content to a file in the media directory
                    with open(image_path, 'wb') as f:
                        f.write(response.content)

                    # Create Image instance and save the URL to the database
                    Images.objects.create(url=url, imagename=imagename)

                    # Return a success response
                    return Response(status=status.HTTP_201_CREATED)

                except RequestException as e:
                    # Handle HTTP request errors
                    raise APIException(detail=f"Failed to download image from {url}")

                except IntegrityError as e:
                    # Handle database integrity error (e.g., duplicate key violation)
                    raise APIException(detail="IntegrityError: Duplicate key or database integrity violation")

                except ValidationError as e:
                    # Handle URL validation error
                    raise APIException(detail="ValidationError: Invalid URL")

                except Exception as e:
                    # Handle other errors (e.g., file write errors)
                    raise APIException(detail="Error processing image")

    def retrieve(self, request, *args, **kwargs):

        try:
             # Get the 'url' parameter from the query parameters
            url = request.query_params.get('url', None)
            
            # Check if the 'url' parameter is missing
            if not url:
                return Response({'error': 'Missing URL parameter'}, status=400)

            # Get the image instance or return a 404 response
            instance = get_object_or_404(Images, url=url)
            imagename = instance.imagename

            # Ensure the media directory exists
            media_directory = os.path.join("media")
            image_path = os.path.join(media_directory, imagename)

            # Check if the image file exists
            if not os.path.exists(image_path):
                return Response({'error': 'Image not found in the media folder'}, status=404)

            # Open the image file and create an HTTP response
            with open(image_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='image/jpeg')
                response['Content-Disposition'] = f'attachment; filename="{imagename}"'

            return response
            
        except ValidationError as e:
            # Handle validation error (ex: invalid URL)
            return Response({'Validation error': str(e)}, status=400)

        except FileNotFoundError:
            # Handle file not found error
            return Response({'error': 'Image file not found in the media folder'}, status=404)

        except Exception as e:
            # Handle unexpected errors
            return Response({'error': 'An unexpected error occurred'}, status=500)
        
    def destroy(self, request, *args, **kwargs):

        try:
            # Get the 'url' parameter from the query parameters
            url = request.query_params.get('url', None)

            # Check if the 'url' parameter is missing
            if not url:
                return Response({'error': 'Missing URL parameter'}, status=400)

            # Get the image instance or return a 404 response
            instance = get_object_or_404(Images, url=url)
            imagename = instance.imagename

            # Ensure the media directory exists
            media_directory = os.path.join("media")
            image_path = os.path.join(media_directory, imagename)

            # Check if the image file exists
            if not os.path.exists(image_path):
                return Response({'error': 'Image not found in the media folder'}, status=404)

            # Delete the instance from the database
            self.perform_destroy(instance)

            # Delete the image file from the media folder
            if os.path.exists(image_path):
                os.remove(image_path)

            return Response(status=204)
        
        except models.ProtectedError:
            # Handle protected error (ex: if there are related objects that prevent deletion)
            return Response({'error': 'Cannot delete image due to related objects'}, status=400)

        except FileNotFoundError:
            # Handle file not found error
            return Response({'error': 'Image file not found in the media folder'}, status=404)

        except PermissionError:
            # Handle permission error (ex: if the process has no permission to delete the file)
            return Response({'error': 'Permission error during deletion'}, status=500)

        except OSError as e:
            # Handle OS error (ex: if the file cannot be removed)
            return Response({'error': f'OS error during deletion: {str(e)}'}, status=500)

        except Exception as e:
            # Handle unexpected errors
            return Response({'error': 'An unexpected error occurred during deletion'}, status=500)
