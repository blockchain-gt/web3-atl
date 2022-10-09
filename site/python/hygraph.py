from python_graphql_client import GraphqlClient
from datetime import datetime
import pandas as pd
import time, random, queries

class Hygraph:

	client = GraphqlClient(endpoint="https://api-us-east-1.hygraph.com/v2/cl6isf8724r4g01uh7l9w44u3/master")

	def __init__(self, fetch_now=True):
		self.speakers = []
		self.speaker_ids = []
		self.speaker_name_to_id = {}
		if fetch_now:
			self.set_speakers()

	def set_speakers(self):
		self.speakers = []
		self.speaker_ids = []
		components = Hygraph.client.execute(query=queries.speakers)["data"]["page"]["components"]
		for component in components:
			if component.get("title", "") == "Speakers":
				for person in component["people"]:
					self.speakers.append(person["name"])
					self.speaker_ids.append(person["id"])
		self.speaker_name_to_id = dict(zip(self.speakers, self.speaker_ids))

	def get_speakers(self):
		if self.speakers:
			return self.speakers
		self.set_speakers()
		return self.speakers

	def _delete_agenda_speakers(self):
		Hygraph.client.execute(query=queries.delete_agenda_speakers, variables=None)
	
	def add_agenda_speakers(self):
		self._delete_agenda_speakers()
		if not self.speakers:
			self.set_speakers()
		for speaker, speaker_id in self.speaker_name_to_id.items():
			Hygraph.client.execute(query=queries.add_agenda_speaker, variables={"id":speaker_id})
		self._publish_agenda_speakers()
		
	def _publish_agenda_speakers(self):
		Hygraph.client.execute(query=queries.publish_agenda_speakers, variables=None)

	def _delete_agenda_items(self):
		Hygraph.client.execute(query=queries.delete_agenda, variables=None)

	def post_agenda(self, agenda_data):
		self._delete_agenda_items()
		self.agenda_item_ids = []
		print('Deleting Agenda Items...')
		for data in agenda_data:
			resp = Hygraph.client.execute(query=queries.add_agenda_item, variables=data)
			self.agenda_item_ids.append(resp['data']['createAgendaItem']['id'])
		print('Publishing Agenda Items...')
		self._publish_agenda()
		print('Adding to Schedule...')
		self._add_agenda_items_to_schedule()
		
	def _publish_agenda(self):
		Hygraph.client.execute(query=queries.publish_agenda_item, variables=None)
		

	def _add_agenda_items_to_schedule(self):
		# for agenda_id in self.agenda_item_ids:
		# 	Hygraph.client.execute(query=queries.upsert_page,variables={'id':agenda_id})
		# Hygraph.client.execute(query=queries.publish_page, variables=None)
		print("\n\nIMPORTANT!!!!")
		print("Manually add agenda items to schedule page\n\n")

if __name__ == "__main__":
	h = Hygraph()

	response = 'None'
	print('\n\n')
	while response not in "nyNY":
		response = input('Create agenda speakers? [Y/N]\n')
	if response.lower() == "y":
		print("Creating Agenda Speakers...")
		h.add_agenda_speakers()

	from google_sheets import Agenda
	a = Agenda()
	df = pd.DataFrame(a.items[1:], columns=a.items[0])
	data = []
	for _, row in df.iterrows():
		title = row["Topic"]
		description = ""
		location = row["Room"]
		hour, minute = row["Start Time"].strip().split(":")
		hour, minute = int(hour), int(minute)
		startTime = datetime(2022,11,int(row["Day"]),hour,minute)
		startTime = startTime.strftime("%Y-%m-%dT%H:%M:00-04:00")
		hour, minute = row["End Time"].strip().split(":")
		hour, minute = int(hour), int(minute)
		endTime = datetime(2022,11,int(row["Day"]),hour,minute)
		endTime = endTime.strftime("%Y-%m-%dT%H:%M:00-04:00")
		category = row["Type"]
		data.append({
			"title":title,
			"description":description,
			"location":location,
			"startTime":startTime,
			"endTime":endTime,
			"category":category
		})

	h.post_agenda(data)