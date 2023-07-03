import React, { useState, useEffect } from "react";
import { Container, ListGroup, Alert, Form, Button } from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import axios from "axios";

const ForwardingRulesPage = () => {
  const [data, setData] = useState([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [newRule, setNewRule] = useState({
    chainName: "",
    rule: {
      target: "",
      protocol: "",
      source: "",
      destination: "",
    },
  });

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Fetch data every 5 seconds

    return () => {
      clearInterval(interval); // Cleanup interval on component unmount
    };
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === "chainName") {
      setNewRule((prevState) => ({
        ...prevState,
        chainName: value,
      }));
    } else {
      setNewRule((prevState) => ({
        ...prevState,
        rule: {
          ...prevState.rule,
          [name]: value,
        },
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      await axios.post("http://localhost:8180/forwarding-chains/add", newRule);

      // Refresh the data after successful POST request
      fetchData();
      setSuccess(true);
      setError("");
    } catch (error) {
      setError("Error adding forwarding rule");
      setSuccess(false);
    }
  };

  const handleClear = async () => {
    try {
      await axios.post("http://localhost:8180/forwarding-chains/clear");
      // Refresh the data after successful clear request
      fetchData();
      setSuccess(true);
      setError("");
    } catch (error) {
      setError("Error clearing forwarding rules");
      setSuccess(false);
    }
  };

  const fetchData = async () => {
    try {
      const response = await axios.get(
        "http://localhost:8180/forwarding-chains/all"
      );
      setData(response.data);
    } catch (error) {
      setError("Error fetching data");
    }
  };

  const chainNames = ["OUTPUT", "INPUT", "FORWARD"]; // Example chain names
  const protocols = ["tcp", "udp", "icmp"]; // Example protocols

  return (
    <Container>
      <CustomNavbar />
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">Request sent successfully!</Alert>}
      <ListGroup>
        {data.map((chain, chainIndex) => (
          <ListGroup.Item key={chainIndex}>
            <h5>{chain.name}</h5>
            <ul>
              {chain.rules.map((rule, ruleIndex) => (
                <li key={ruleIndex}>
                  <strong>Rule {ruleIndex + 1}</strong>
                  <ul>
                    <li>Command: {rule.command}</li>
                    <li>Target: {rule.target}</li>
                    <li>Protocol: {rule.protocol}</li>
                    <li>Options: {rule.options}</li>
                    <li>Source: {rule.source}</li>
                    <li>Destination: {rule.destination}</li>
                  </ul>
                </li>
              ))}
            </ul>
          </ListGroup.Item>
        ))}
      </ListGroup>

      <h2>Add Forwarding Rule</h2>
      <Form onSubmit={handleSubmit}>
        <Form.Group controlId="chainName">
          <Form.Label>Chain Name</Form.Label>
          <Form.Control
            as="select"
            name="chainName"
            value={newRule.chainName}
            onChange={handleChange}
          >
            <option value="">Select Chain Name</option>
            {chainNames.map((chainName) => (
              <option key={chainName} value={chainName}>
                {chainName}
              </option>
            ))}
          </Form.Control>
        </Form.Group>
        <Form.Group controlId="target">
          <Form.Label>Target</Form.Label>
          <Form.Control
            type="text"
            name="target"
            value={newRule.rule.target}
            onChange={handleChange}
          />
        </Form.Group>
        <Form.Group controlId="protocol">
          <Form.Label>Protocol</Form.Label>
          <Form.Control
            as="select"
            name="protocol"
            value={newRule.rule.protocol}
            onChange={handleChange}
          >
            <option value="">Select Protocol</option>
            {protocols.map((protocol) => (
              <option key={protocol} value={protocol}>
                {protocol}
              </option>
            ))}
          </Form.Control>
        </Form.Group>
        <Form.Group controlId="source">
          <Form.Label>Source</Form.Label>
          <Form.Control
            type="text"
            name="source"
            value={newRule.rule.source}
            onChange={handleChange}
          />
        </Form.Group>
        <Form.Group controlId="destination">
          <Form.Label>Destination</Form.Label>
          <Form.Control
            type="text"
            name="destination"
            value={newRule.rule.destination}
            onChange={handleChange}
          />
        </Form.Group>
        <Button type="submit">Add Rule</Button>
      </Form>

      <h2>Clear Forwarding Rules</h2>
      <Button variant="danger" onClick={handleClear}>
        Clear Rules
      </Button>
    </Container>
  );
};

export default ForwardingRulesPage;
