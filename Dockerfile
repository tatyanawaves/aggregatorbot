# Start with a base Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the necessary files into the container
COPY main.py ai_tools.db config.py database.py openai_client.py requirements.txt /app/

# Install any dependencies required by main.py
# Uncomment and edit the line below if you have a requirements file
# COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Set config.py to read-only
RUN chmod 444 /app/config.py

# Expose a port if your application requires it, for example, 8000
# EXPOSE 8000

# Run the main application
CMD ["python", "main.py"]
