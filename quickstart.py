from __future__ import print_function
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

testEvent = {
    'start': {
    'dateTime': '2016-03-05T09:00:00-07:00',
    'timeZone': 'America/Los_Angeles',
    },
    'end': {
    'dateTime': '2016-03-05T17:00:00-07:00',
    'timeZone': 'America/Los_Angeles',
    }
}
event2 = {
  'summary': 'Google I/O 2 2016',
  'location': '800 Howard St., San Francisco, CA 94103',
  'description': 'A chance to hear more about Google\'s developer products.',
  'start': {
    'dateTime': '2016-03-05T09:00:00-07:00',
    'timeZone': 'America/Los_Angeles',
  },
  'end': {
    'dateTime': '2016-03-05T17:00:00-07:00',
    'timeZone': 'America/Los_Angeles',
  },
  'recurrence': [
    'RRULE:FREQ=DAILY;COUNT=2'
  ],
  'reminders': {
    'useDefault': False,
    'overrides': [
      {'method': 'email', 'minutes': 24 * 60},
      {'method': 'popup', 'minutes': 10},
    ],
  },
}

defaultWorkBlock = 1 # 1 hour

#priority: 1-10, 1 is highest
#estimatedDuration in hours
assignments = [
    { 'name' : 'A1', 'dueDate' : datetime.datetime(2016, 3, 7, 10), 'priority' : 1, 'estimatedDuration' : 5, 'timeRemaining': 5},
    { 'name' : 'A2', 'dueDate' : datetime.datetime(2016, 3, 6, 10), 'priority' : 1, 'estimatedDuration' : 4, 'timeRemaining' : 4}
]

# global free time list
freeTime = []

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def getBlockLength(block):
    return block['end'] - block['start']

def getWorkBlock(length):
	# input an duration
	# returns a workblock: which is a dict consisting of start and end datetime
	# functionality: cycle through the list of freeblocks until a suitable chunk is found and allocate
    workBlock = {}
    foundBlock = False

    for idx, freeBlock in enumerate(freeTime):
        if getBlockLength(freeBlock) >= datetime.timedelta(hours=length):
            # make work block
            workBlock['start'] = freeBlock['start']
            workBlock['end'] = workBlock['start'] + datetime.timedelta(hours=length)

            # update free time
            if (freeBlock['start'] + datetime.timedelta(hours=length) < freeBlock['end']): # is there time left in block
                freeTime[idx]['start'] += datetime.timedelta(hours=length)
            else: # free block filled, remove it
                freeTime.pop(idx)

            foundBlock = True
            break

    if (foundBlock == False):
        print("No free time left")
        return -1
    else:
        return workBlock 


def addToCalendar(workBlocks, service):
    print("Adding work blocks to the calendar")
    for workBlock in workBlocks:
        new_event = service.events().insert(calendarId='primary', body=workBlock).execute()
        
		
def allocateTime(assignments):
    #input the list of assignments to be allocated#outputs a list of blocks, representing the proposed scheduling of assignments
    #functionality: splits the freetime blocks into work blocks
    # freetime is global
    output = [];
    for idx, assignment in enumerate(assignments):
        #duration = assignment['estimatedDuration'] #in hours
        timeRemaining = assignment['timeRemaining']
        while (timeRemaining > 0):
            for freeBlock in freeTime:
                check = datetime.timedelta(hours = defaultWorkBlock)			
                if freeBlock['start'] + check < assignment['dueDate']: #only if its before due date		
                    if(timeRemaining < defaultWorkBlock):
                        workBlock = getWorkBlock(timeRemaining)
                        timeRemaining = 0
                    elif (timeRemaining == defaultWorkBlock):
                        workBlock = getWorkBlock(defaultWorkBlock)
                        timeRemaining -= defaultWorkBlock
                    else: # assignment takes more than defaultWorkBlock to complete
                        workBlock = getWorkBlock(defaultWorkBlock)
                        timeRemaining -= defaultWorkBlock					
                workBlock['summary'] = assignment['name']
                output.append(workBlock)	
    return output

def main():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    max_event_dateTime = datetime.datetime.utcnow() + datetime.timedelta(days=5) # furthest time in future to fetch events
    max_formatted = max_event_dateTime.isoformat() + 'Z' 

    print('Getting the upcoming events for the next day')

    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, timeMax=max_formatted, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    eventTimes = []

    if not events:
        print('No upcoming events found.')
    for event in events:
        
        print(event['start']['dateTime'])
        #print(event['summary'])
        start = event['start'].get('dateTime', event['start'].get('date'))
        #eventTimes.append([event['summary'], event['start']['dateTime'], event['end']['dateTime']
        #print(start, event['summary'])

    events.sort(key=lambda r: r['start']['dateTime'])

		
		
	

    for idx, event in enumerate(events):
        if idx < len(events)-1: #if we don't have the last event
            freeBlockStart = datetime.datetime.strptime(event['end']['dateTime'],"%Y-%m-%dT%H:%M:%S-05:00") # ****assumes UTC-5******
            freeBlockEnd = datetime.datetime.strptime(events[idx+1]['start']['dateTime'],"%Y-%m-%dT%H:%M:%S-05:00") # ****assumes UTC-5******
            freeTime.append({'start' : freeBlockStart, 'end' : freeBlockEnd})
        else: # for the last event
            freeBlockStart = datetime.datetime.strptime(event['end']['dateTime'],"%Y-%m-%dT%H:%M:%S-05:00") # ****assumes UTC-5******
            #print(endTime)
            #print(max_event_dateTime)
            if freeBlockStart < max_event_dateTime:
                freeTime.append({ 'start' : freeBlockStart, 'end' : max_event_dateTime})

    print("Free Time Blocks\n")
    for freeBlock in freeTime:
        print(freeBlock['start'].strftime("Start: %H:%M, %b %d, %Y"))
        print(freeBlock['end'].strftime("End: %H:%M, %b %d, %Y"))
    
    assignments.sort(key=lambda r: r['priority'], reverse=True) #sort assignment by priority, reverse since 1 is highest priority
    
    print("Allocating Assignments\n")
    test = allocateTime(assignments)
    for block in test:
        print(block['summary'])
        print(block['start'].strftime("Start: %H:%M, %b %d, %Y"))
        print(block['end'].strftime("End: %H:%M, %b %d, %Y"))
		        

    """
    for idx, assignment in enumerate(assignments):
        duration = assignment['estimatedDuration']

        if (duration < defaultWorkBlock):
            workBlock = getWorkBlock(duration)

            print("Assignment assigned to time")
            print(workBlock)

        elif (duration == defaultWorkBlock):
            workBlock = getWorkBlock(defaultWorkBlock)

            print("Assignment assigned to time")
            print(workBlock)

        else: # assignment takes more than defaultWorkBlock to complete
            print(assignments[idx])

            workBlock = getWorkBlock(defaultWorkBlock)

            assignments[idx]['timeRemaining'] -= defaultWorkBlock

            print("Assignment assigned to time")
            print(workBlock)
	"""
	
    print("Printing Free Time Blocks\n")
    for freeBlock in freeTime:
	
        print(freeBlock['start'].strftime("Start: %H:%M, %b %d, %Y"))
        print(freeBlock['end'].strftime("End: %H:%M, %b %d, %Y"))

    #addToCalendar(test, service)


    
    new_event = service.events().insert(calendarId='primary', body=testEvent).execute()

    #print "Event created: %s" % (event.get('htmlLink'))


if __name__ == '__main__':
    main()
