1. Add the Jaeger Helm repository

helm repo add jaeger-all-in-one https://raw.githubusercontent.com/hansehe/jaeger-all-in-one/master/hel

2. Install Jaeger using your custom values.yaml file

helm install jaeger-all-in-one -f values.yaml jaeger-all-in-one/jaeger-all-in-one \
  --namespace jaeger-tracing \
  --create-namespace

✅ Configure Local hosts File on Windows
1. Open Notepad as Administrator
Open the Start Menu
Search for "Notepad"
Right-click on Notepad → Choose "Run as administrator"


2. Open the hosts file
In Notepad, go to: File → Open → Navigate to: C:\Windows\System32\drivers\etc\
Make sure to select "All Files (.)" in the file picker
Open the file named hosts


3. Add your custom hostname mapping
Scroll to the bottom and add this line:
34.69.203.236 jaeger.vmt.com


4. Save the file
Use Ctrl+S or File → Save