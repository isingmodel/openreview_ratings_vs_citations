import openreview
import json

client = openreview.Client(baseurl="https://api.openreview.net")

# Fetch a sample of notes to see invitations
print("Listing invitations from sample notes...")
notes = list(openreview.tools.iterget_notes(client, invitation='ICLR.cc/2019/Conference/-/.*', limit=200))

invitations = set()
for n in notes:
    invitations.add(n.invitation)

for i in sorted(invitations):
    print(i)
