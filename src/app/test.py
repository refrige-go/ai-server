import os
print(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
print(os.path.exists(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")))