# The Notification Service

The Notification Service is a way for data to be pushed to and from FME Server in the form of short messages.

**What is a Notification?**

A notification is a simple message (sometimes called an “alert”) that informs someone or something that a particular event has happened.

Notifications on FME Server can occur in two different forms; incoming and outgoing.

Incoming notifications alert FME Server to an event that has taken place elsewhere.

Outgoing notifications alert users to an event that has taken place on FME Server.

In this way, FME Server can take action in response to an event notification, or a user can take action in response to a notification from FME Server.

The **Notification Service** is the part of the FME Server architecture that handles incoming and outgoing notifications.

**When to Use Notifications**

Notifications should be used when you want to trigger an FME Server response to an event that is reported from outside of FME. The event should not be a continuous series of messages; if there is more than one message per second you should consider using Message Streaming techniques instead.

Notifications are also for when you want to send a message about something that happened on FME Server, to an outside subscriber. Again, if there is likely to be more than one message per second you should consider using Message Streaming.

In either case a notification is for sending a brief message, usually in order to trigger an action from the recipient. It’s not intended to be used for transmitting large amounts of spatial data. At most you should use it for a single geographic feature such as a point location.

**Elements of the Notification Service**

The Notification Service includes a number of different components.

• Clients An external user or system that sends or receives a notification

• Publications An event handler that listens for incoming notifications

• Subscriptions An event handler that dispatches outgoing notifications

• Topics A subject that describes what the notification is about

• Protocols Methods by which FME Server can receive or send notifications

Although the diagram below shows a continuous process, from a sending client through FME Server to a receiving client, it is not necessary for all of these components to be used in a setup.

If the system is designed for FME Server to only receive notifications, then only the publications side of the diagram is relevant. Likewise, if the system is intended for FME Server to only send notifications, then only the subscriptions side of the diagram applies.

**Clients**

A client is a user or system that sends or receives a notification. The client may be a physical person, or may just be a component in a computer system.

For example, a database update might cause a trigger to send a notification to FME Server, in which case the database system is the client. But a client could also be a person who, for example, triggers a notification by sending an email to FME Server.

Since they are sending information these clients are called “Publishers”.

Likewise, FME Server can send a notification for another client system to receive. Alternatively this client can also be a real person, who might receive a notification in the form of an email.

Since they are receiving information, these clients are called “Subscribers”.

**Publications**

A Publication is a component that receives incoming notifications from a client.

To receive notification in FME Server a user must create a new Publication. A Publication is created in the FME Server Web User Interface under the Notifications section.

**Topics**

A Topic is a component that acts as a mediator for messages and defines the message content. Think of it as a subject line for notifications.

Like Publications, a Topic is created in the FME Server Web User Interface, under the Notifications section.

All Publications are linked to one (or more) Topics, so that when an incoming message is received it is categorized and the related Topic is triggered.

Because a Publication can be linked to multiple Topics, each incoming message can trigger multiple actions to occur. Additionally, multiple Publications can trigger the same topic.

For example, a lightning strike sensor might publish to the topics WeatherEvent and AircraftAlerts, whereas a flood sensor might publish to the topics WeatherEvent and RoadConditions.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Daily Interop Reporter, Chad Pugh-Litzer says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“It’s like when I write a news article. I publish the article to the Daily
Interop web site, tagged with a number of topics to describe it.
For example, a report about a soccer team’s tax return would be filed
under both ‘Financial’ and ‘Sports’ because it relates to both.”
</span>
</td>
</tr>
</table>

**Subscriptions**

A Subscription is a component that sends outgoing notifications to a client.

To send a notification in FME Server a user must create a new Subscription.

A Subscription is created in the FME Server web interface under the Notifications section.

As with Publications, each Subscription is also tied to one (or more) Topics, and each Topic can be subscribed to by multiple Subscriptions.

For example, a police headquarters might subscribe to the RoadConditions topic, to receive notifications on that subject. The local TV weather channel also subscribes to the RoadConditions topics, but in addition subscribes to WeatherEvent to hear about those particular events.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">InteropGeek68 says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“I subscribe to articles published on the Daily Interop web site
according to their topic.
For example, I subscribe to reports on technology and gaming,
whereas my friend – InteropJock72 – subscribes to sports articles”
</span>
</td>
</tr>
</table>

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">IMPORTANT</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
This is text as spoken by a person from the city of Interopolis
<br>Although the actions seem odd in regard to the name – Publications receive
messages, Subscriptions send them – it is correct. The name refers to the Client, not
the Server.
So FME Server receives a Publication because the client is publishing it.
Likewise, FME Server sends a Subscription because the client is subscribing to it.
</span>
</td>
</tr>
</table>

**Protocols**

A protocol is a system of data exchange between FME Server and a client. It is the method by which FME Server receives notifications from a client and sends notifications to a client.

E-mail is a messaging protocol, as are Apple and Android alerts.

Each Publication and Subscription must be defined using a particular communication protocol. An e-mail Publication – for example – will accept notifications via an incoming email message. An Apple Subscription will send notifications to an Apple mobile device.

Protocols are pre-defined components in the FME Server architecture and do not need to be defined in the Web User Interface.

However, a number of fields are made available to configure them when a Publication or Subscription chooses to make use of that protocol.

For example, here are the parameters for an e-mail Subscription.

These parameters must be set when the Subscription is created as they are needed in order to be able to send out a notification using the e-mail protocol.