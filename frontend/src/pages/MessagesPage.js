import axios from "axios";
import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Container, ListGroup } from "react-bootstrap";
import { IoCubeOutline } from "react-icons/io5";
import CustomNavbar from "../components/CustomNavbar";
import { BACKEND_URL } from "../config/BackendConfiguration";

const MessagesPage = () => {
  const [data, setData] = useState([]);
  const [error, setError] = useState(null);
  const [messages, setMessages] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState("all");
  const [groupIds, setGroupIds] = useState([]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Fetch data every 5 seconds

    return () => {
      clearInterval(interval); // Clean up the interval on component unmount
    };
  }, []);

  useEffect(() => {
    setMessages(data.filter((message) => message.groupId === selectedGroupId));
  }, [selectedGroupId]);

  const fetchData = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/messages/all`);
      setData(response.data);
      setError(null);

      setGroupIds(
        response.data.reduce((acc, curr) => {
          if (!acc.includes(curr.groupId)) {
            acc.push(curr.groupId);
          }
          return acc;
        }, [])
      );

      if (selectedGroupId === "all") {
        setMessages(response.data);
      }

      if (selectedGroupId !== "all") {
        setMessages(
          response.data.filter((message) => message.groupId === selectedGroupId)
        );
      }
    } catch (error) {
      setError("Failed to fetch messages.");
    }
  };

  const handleClearMessages = async () => {
    try {
      await axios.get(`${BACKEND_URL}/messages/clear`);
      setData([]);
      setError(null);
    } catch (error) {
      setError("Failed to clear messages.");
    }
  };

  // Group messages by source and destination
  const getGroupedMessages = () => {
    var filteredMessages = data.filter(
      (group) => group.groupId === selectedGroupId
    );

    if (filteredMessages.length !== 1) {
      return [];
    }

    filteredMessages = filteredMessages[0].messages;

    const groupedMessages = {};

    filteredMessages.forEach((message) => {
      const key = `${message.src_ip}-${message.dst_ip}`;
      if (groupedMessages[key]) {
        groupedMessages[key].count += 1;
      } else {
        groupedMessages[key] = {
          message,
          count: 1,
        };
      }
    });

    // Transform object into array
    const groupedMessagesArray = Object.values(groupedMessages);

    return groupedMessagesArray;
  };

  return (
    <Container>
      <CustomNavbar />
      <Card className="my-4">
        <Card.Body>
          <h3>Messages Page</h3>
          {error && <Alert variant="danger">{error}</Alert>}
          {groupIds.length === 0 && !error && (
            <Alert variant="info">No messages available.</Alert>
          )}
          <Button variant="danger" onClick={handleClearMessages}>
            Clear Messages
          </Button>

          <hr />

          <div style={{ overflowX: "scroll", display: "flex" }}>
            {groupIds.map((groupId) => (
              <Button
                key={groupId}
                style={{
                  margin: "0 5px",
                  width: "180px",
                  height: "180px",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  position: "relative",
                }}
                variant={
                  selectedGroupId === groupId ? "primary" : "outline-primary"
                }
                onClick={() => setSelectedGroupId(groupId)}
              >
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: "50%",
                    transform: "translateX(-50%)",
                  }}
                >
                  <IoCubeOutline size={40} />
                </div>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    height: "100%",
                  }}
                >
                  <span>{groupId}</span>
                </div>
              </Button>
            ))}
          </div>

          <hr />

          {messages.length > 0 ? (
            <ListGroup className="mt-4">
              {getGroupedMessages().map(({ message, count }, index) => (
                <ListGroup.Item key={index}>
                  <div>
                    <p>Protocol: {message.protocol}</p>
                    <p>Source IP: {message.src_ip}</p>
                    <p>Destination IP: {message.dst_ip}</p>
                    <p>Source Port: {message.src_port || "N/A"}</p>
                    <p>Destination Port: {message.dst_port || "N/A"}</p>
                    <p>Count: {count}</p>
                  </div>
                </ListGroup.Item>
              ))}
            </ListGroup>
          ) : (
            <Alert variant="info">No messages available for this group.</Alert>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default MessagesPage;
