# Use the official Python image from the Docker Hub
FROM python:3.12.4

# Set environment variables to prevent Python from writing .pyc files
# and to ensure that output is sent straight to terminal (e.g. for logs).
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application into the container
COPY . .

# Expose the port that the app runs on
EXPOSE 8000




# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]