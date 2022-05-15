#!/usr/bin/python
""" pubsub.py -- very cheap publish/subscribe

Copyright (C) 2012 Phil Mayes
See COPYING.txt for licensing information

Contact: phil@philmayes.com

Topics are string keys in a dictionary. The value for a topic is in turn
a dictionary whose keys are the registered callback functions. Their values
have no meaning.
"""
topics = {}


def publish(topic, *args, **kwargs):
    if topic in topics:
        for consumer in topics[topic]:
            consumer(*args, **kwargs)


def subscribe(topic, consumer):
    """Register callable <consumer> for string <topic>."""
    # add topic to the dictionary if it does not yet exist
    if not topic in topics:
        topics[topic] = {}
    # get the dictionary of consumers for this topic
    consumers = topics[topic]
    # register this consumer
    consumers[consumer] = 1


def unsubscribe(topic, consumer):
    """Remove topic + consumer from the dictionary if it exists."""
    if topic in topics:
        # remove consumer for this topic; OK if does not exist
        topics[topic].pop(consumer, 0)


def test():
    def callback1(data):
        print("callback1", data)

    def callback2(data, d2):
        print("callback2", data, d2)

    def callback3(*args, **kwargs):
        print("callback3", args, kwargs)

    # subscribe the above callbacks to various topics
    subscribe("alpha", callback1)
    subscribe("beta", callback2)
    subscribe("beta", callback3)
    subscribe("unpublished", callback3)

    # publish various topics
    publish("alpha", 111)
    publish("beta", [12, 23, 34], "string!")
    publish("gamma", "three")

    print(topics)
    unsubscribe("beta", callback3)
    print(topics)


if __name__ == "__main__":
    test()
