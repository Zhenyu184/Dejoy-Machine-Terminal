import requests
import json

url = "http://163.13.133.185:3000/updateUrl"

payload = json.dumps({
  "events": [
    {
      "type": "ngrokUrl",
      "timestamp": 1661598664448,
      "source": {
        "vendorHwid": "dj11300111",
        "ngrokUrl": "http://555888888888885133-72.ngrok.io"
      }
    }
  ]
})
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)












