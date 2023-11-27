# Image Download Service
The task is to implement a web service with a REST interface (preferably in python). The service should offer 3 REST operations with following conditions.

1. Uploading list of image urls and downloading the corresponding images
- Given a list of image urls. When the user sends this list to the service via http, the service starts downloading the images. The service puts the images into a storage, so that they can be listed by and retrieved from the service, see below operation 2. & 3. There is no need to handle download errors: should a link to the image be wrong or the image can not be downloaded, it is just left out. The storage should be persistent, i.e. not in memory.

2. Get the list of available images
- When the user calls this operation via http,the service replies with a list of all images that had been (sucessfully) processed via calls to the previous operation 1.

3. Retrieve an image

- Given that there were previously images processed via operation 1, when the user calls this operation with an url as an input-parameter, then the service sends the corresponding image, if it was stored previously via operation 1.

- Throughout operation 1-3, the key of images should always be the full url that was used in the original input list for operation 1

# Tech stacks used:
- Python
- Django Rest Framework
- Postgresql

# Implementation Architecture
Local system approach architecture of this task has been has been provided in the JPG file "Implementation_Architecture"

# Cloud Based Implementation Architecture
Cloud based approach architecture of this task using AWS has been provided in the JPG file "Cloud_Based_Implementation_Architecture".

# Added Features
Apart from the given tasks, the following features has also been added.
- "Authentication and authorization" using Token based authentication in Django Rest Framework. To access the API endpoints, the user must register themselves with username, email-ID and password. And then login with the same credentials to get the access token to consume the API endpoints.
- "Delete a particular image" - this feature will expect an url from the user and checks the database whether the image url already exists, if it exists then it will delete the entry as well as the actual image.

# API endpoints
Below is the API endpoint for task 1 to get image URLs from the user and save the metadata in database as well as in the file system. You can replace the image URLs in the command below with yours accordingly.

```bash
curl -X POST http://localhost:9000/api/images/ -H "Content-Type: application/json" -H "Authorization: Token YOUR_ACCESS_TOKEN" -d '{
  "image_urls": [
    "https://picsum.photos/id/1/200/300",
    "https://picsum.photos/id/2/200/300",
    "https://picsum.photos/id/3/200/300"
  ]
}'
```

Below is the API endpoint for task 2 to list all available images.

```bash
curl -H "Authorization: Token <your_token> " http://localhost:9000/api/images/
```

Below is the API endpoint for task 3 to retrieve an image by giving the image URL as an input parameter.

```bash
curl -H "Authorization: Token <your_token>" "http://localhost:9000/api/image?url=<your_image_url>"
```

Below is the API endpoint for the added feature "Delete an image from the storage with image URL as an input parameter".

```bash
curl -X DELETE "http://localhost:9000/api/image?url=https://picsum.photos/id/1/200/300" -H "Authorization: Token <your_token>"
```
