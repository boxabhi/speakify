from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json
from django.contrib.auth import get_user_model
User = get_user_model()

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.cache import cache
import random
import uuid
from channels.auth import login
from django.conf import settings
import sys, os
from django.core.cache.backends.base import DEFAULT_TIMEOUT
CACHE_TTL = getattr(settings ,'CACHE_TTL' , DEFAULT_TIMEOUT)



class UserRoom(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'user_{self.room_name}'
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )
        self.accept()

        print("****")
        print(cache.get("active_users"))
        print(cache.get("active_users_with_interests"))
        print("****")


        self.send(text_data=json.dumps({
            'payload': {}
        }))
    
    def receive(self,text_data):
        data = json.loads(text_data)

        if data.get('type') == 'connect_person':
            async_to_sync(self.channel_layer.group_send)(
                f"user_{data.get('user_id')}",
                {
                    'type': 'connect_with_someone',
                    'value': json.dumps(data),
                },
            )


    def connect_with_someone(self , text_data):
        try:
            data = json.loads(text_data['value'])
            print('@@@')

            print(data)
            print('@@@')
            requested_user = User.objects.get(id = self.room_name)
            user_id = self.room_name
            online_users = cache.get("active_users")
            print("*********************")

            print(online_users)
            print(type(online_users))

            print("*********************")

            matching_users = User.objects.filter(
                is_online = True,
                interests__in = requested_user.interests.all()
                #id__in =
                ).exclude(id = user_id).distinct()
            
            random_user = None
            if matching_users.exists():
                random_user = random.choice(matching_users)
            else:
                matching_users = User.objects.filter(
                is_online = True).exclude(id = user_id).distinct()

                if matching_users:
                    random_user = random.choice(matching_users)

            print(")))))))))))))))")
            print(random_user)

            print(")))))))))))))))")

        
            if  random_user is None:
                async_to_sync(self.channel_layer.group_send)(
                'user_%s' % user_id,{
                    'type':'accept_request',
                    'value': json.dumps({
                        "found" : False,
                    }),})
                return


            chat_room_code =  str(uuid.uuid4())

            async_to_sync(self.channel_layer.group_send)(
                'user_%s' % requested_user.id,{
                    'type':'accept_request',
                    'value': json.dumps({
                        "found" : True,
                        "user_id" : random_user.id,
                        "interests" : random_user.get_interests(),
                        "country" : random_user.country,
                        "full_name" : random_user.full_name,
                        "phone_number" : random_user.phone_number,
                        "gender" : random_user.gender,
                        "status" : True,
                        "connected" : False,
                        "chat_room_code" :chat_room_code
                    }),})
            
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
           

        async_to_sync(self.channel_layer.group_send)(
            'user_%s' % random_user.id,{
                'type':'accept_request',
                'value': json.dumps({
                     "found" : True,

                    "user_id" : requested_user.id,
                    "interests" : requested_user.get_interests(),
                    "country" : requested_user.country,
                    "full_name" : requested_user.full_name,
                    "phone_number" : requested_user.phone_number,
                    "gender" : requested_user.gender,
                    "status" : True,
                    "connected" : False,
                    "chat_room_code" :chat_room_code

                }),})



    def accept_request(self , text_data):
        print("**")
        data = json.loads(text_data['value'])
        print(text_data)
        print("**")
        self.send(text_data = json.dumps({
            'payload': data,
            "message" : "random user found"
        }))

    def disconnect(self,close_code):
        pass

class OnlinePool(WebsocketConsumer):
    active_users = set()
    active_users_with_interests = []

    def add_user_to_online_pool(self , user_id):
        user = User.objects.get(id = self.user_id)
        user.is_online = True
        user.save()
        if user_id in self.active_users:
            return 
        self.active_users.add(user_id)


        print("ONLINE SET")

        self.active_users_with_interests.append({
            "user_id" : self.user_id,
            "interests" : user.get_interests(),
            "country" : user.country,
            "full_name" : user.full_name,
            "phone_number" : user.phone_number,
            "gender" : user.gender,
            "status" : True,
            "connected" : False
        })

        cache.set("active_users_with_interests" , self.active_users_with_interests)
        cache.set("active_users" , self.active_users)

    def del_user_from_online_pool(self, user_id):
        i = 0
        user = User.objects.get(id = self.user_id)
        user.is_online = False
        user.save()
        for active_users in self.active_users_with_interests:
            if active_users['user_id'] == user_id:
                del self.active_users_with_interests[i]
                self.active_users.remove(user_id)
                break
            i = i + 1


        
        cache.set("active_users_with_interests" , self.active_users_with_interests)
        cache.set("active_users" , self.active_users)


    def connect(self):
        self.room_name = "online_pool"
        self.room_group_name = "online_pool_group"
     
        self.user_id = str(self.scope['query_string'].decode('utf-8').split("=")[1])
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

        self.add_user_to_online_pool(self.user_id)

        print(self.active_users_with_interests)
        
        self.send(text_data=json.dumps({
            'status' : 'connected from django channels',
            "active_users" : self.active_users_with_interests            
            }))
        
    
    
    def receive(self, text_data):
        data = json.loads(text_data)
        self.user = self.scope["user"]
        if data.get('type') == 'toggle_status':
            async_to_sync(self.channel_layer.group_send)(
                "online_pool_group",{
                    'type':'toggle_status',
                    'value': json.dumps(data),
                    }
                )


      
        self.send(text_data=json.dumps({'status' : 'we got you'}))

    def toggle_status(self , text_data):
        data = json.loads(text_data['value'])
        user_id = data['user_id'] 
        status = False
        if user_id in self.active_users:
           print("YESS")
           self.del_user_from_online_pool(user_id)
        else:
            print("NOO")

            self.add_user_to_online_pool(user_id)
            status = True


        print(self.active_users_with_interests)
        self.send(text_data=json.dumps({
            'payload': data,
            "active_users" : self.active_users_with_interests,
            "status" : status
        }))

    def disconnect(self , *args, **kwargs):
        user = User.objects.get(id = self.user_id)
        user.is_online = False
        user.save()
    
    
    def send_notification(self , event):
        print('send notification')
        data = json.loads(event.get('value'))
        self.send(text_data=json.dumps({'payload' : data}))
        
        print('send notification')



class NewConsumer(AsyncJsonWebsocketConsumer):
    
    async def connect(self):
        self.room_name = 'new_consumer'
        self.room_group_name = "new_consumer_group"
        
        await(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        self.user = self.scope["user"]
        print(self.user)
        await self.send(text_data=json.dumps({'status' : 'connected from new async json consumer'}))
        
        
    async def receive(self, text_data):
        print(text_data)
        #await self.send(text_data=json.dumps({'status' : 'we got you'}))


    async def disconnect(self , *args, **kwargs):
        await print('disconnected')
    
    async  def send_notification(self , event):
        data = json.loads(event.get('value'))
        await self.send(text_data=json.dumps({'payload' : data}))
        
    
    
    

class ChatMessage(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['chat_room_id']
        self.group_name = self.room_name
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )
        self.accept()

        self.send(text_data=json.dumps({
            'payload': {}
        }))
    
    def receive(self,text_data):
        data = json.loads(text_data)

        print(data)

        async_to_sync(self.channel_layer.group_send)(
            self.room_name,
            {
                'type': 'message',
                'value': json.dumps(data),
            },
        )

    def message(self , event):
        print('send notification')
        data = json.loads(event.get('value'))
        print(data)
        self.send(text_data=json.dumps({'payload' : data}))
        
        print('send notification')
