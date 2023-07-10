import React, { useState, useEffect } from "react";
import {
  Container,
  ListGroup,
  Alert,
  Form,
  Button,
  Card,
} from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import axios from "axios";
import { BACKEND_URL } from "../config/BackendConfiguration";

const ForwardingRulesPage = () => {
  const [data, setData] = useState([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [selectedContainer, setSelectedContainer] = useState("");
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
    const interval = setInterval(fetchData, 5000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  const handleChange = (e) => {
    setSelectedContainer(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      await axios.post(`${BACKEND_URL}/forwarding-chains/add`, newRule);
      fetchData();
      setSuccess(true);
      setError("");
      setTimeout(() => {
        setSuccess(false);
      }, 3000);
    } catch (error) {
      setError("Error adding forwarding rule");
      setSuccess(false);
    }
  };

  const handleClear = async () => {
    try {
      await axios.post(`${BACKEND_URL}/forwarding-chains/clear`);
      fetchData();
      setSuccess(true);
      setError("");
      setTimeout(() => {
        setSuccess(false);
      }, 3000);
    } catch (error) {
      setError("Error clearing forwarding rules");
      setSuccess(false);
    }
  };

  const fetchData = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/forwarding-chains/all`);
      setData(response.data);
    } catch (error) {
      setError("Error fetching data");
    }
  };

  const chainNames = ["OUTPUT", "INPUT", "FORWARD"];
  const protocols = ["tcp", "udp", "icmp"];

  const filteredData = selectedContainer
    ? data.filter((container) => container.containerId === selectedContainer)
    : data;

  const getRulesGroupedByChain = (rules) => {
    const rulesGroupedByChain = {};
    rules.forEach((rule) => {
      if (!rulesGroupedByChain[rule.chain]) {
        rulesGroupedByChain[rule.chain] = [];
      }
      rulesGroupedByChain[rule.chain].push(rule);
    });
    return rulesGroupedByChain;
  };

  return (
    <Container>
      <CustomNavbar />
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">Request sent successfully!</Alert>}

      <Card className="my-4">
        <Card.Body>
          <h3>Forwarding Rules</h3>
          <Form.Group controlId="containerSelect">
            <Form.Label>Container</Form.Label>
            <Form.Control
              as="select"
              value={selectedContainer}
              onChange={handleChange}
            >
              <option value="">All Containers</option>
              {data.map((container) => (
                <option
                  key={container.containerId}
                  value={container.containerId}
                >
                  {container.containerName}
                </option>
              ))}
            </Form.Control>
          </Form.Group>
          {filteredData.length > 0 ? (
            <ListGroup>
              {filteredData.map((container) => (
                <ListGroup.Item key={container.containerId}>
                  <h5>{container.containerName}</h5>
                  {Object.entries(getRulesGroupedByChain(container.rules)).map(
                    ([chain, rules]) => (
                      <Card key={chain} className="my-3">
                        <Card.Body>
                          <Card.Title>{chain}</Card.Title>
                          {rules.map((rule, ruleIndex) => (
                            <Card key={ruleIndex} className="my-3">
                              <Card.Body>
                                <Card.Title>Rule {ruleIndex + 1}</Card.Title>
                                <Card.Text>Chain: {rule.chain}</Card.Text>
                                <Card.Text>Command: {rule.command}</Card.Text>
                                <Card.Text>Target: {rule.target}</Card.Text>
                                <Card.Text>Protocol: {rule.protocol}</Card.Text>
                                <Card.Text>Options: {rule.options}</Card.Text>
                                <Card.Text>Source: {rule.source}</Card.Text>
                                <Card.Text>
                                  Destination: {rule.destination}
                                </Card.Text>
                              </Card.Body>
                            </Card>
                          ))}
                        </Card.Body>
                      </Card>
                    )
                  )}
                </ListGroup.Item>
              ))}
            </ListGroup>
          ) : (
            <p>No forwarding rules found.</p>
          )}
        </Card.Body>
      </Card>

      <Card className="my-4">
        <Card.Body>
          <h3>Add Forwarding Rule</h3>
          <Form onSubmit={handleSubmit}>
            <Form.Group controlId="containerName">
              <Form.Label>Container Name</Form.Label>
              <Form.Control
                as="select"
                name="containerName"
                value={newRule.containerName}
                onChange={(e) =>
                  setNewRule({ ...newRule, containerId: e.target.value })
                }
              >
                <option value="">Select Container Name</option>
                {data.map((container) => (
                  <option
                    key={container.containerId}
                    value={container.containerId}
                  >
                    {container.containerName}
                  </option>
                ))}
              </Form.Control>
            </Form.Group>
            <Form.Group controlId="chainName">
              <Form.Label>Chain Name</Form.Label>
              <Form.Control
                as="select"
                name="chainName"
                value={newRule.chainName}
                onChange={(e) =>
                  setNewRule({ ...newRule, chainName: e.target.value })
                }
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
                onChange={(e) =>
                  setNewRule({
                    ...newRule,
                    rule: { ...newRule.rule, target: e.target.value },
                  })
                }
              />
            </Form.Group>
            <Form.Group controlId="protocol">
              <Form.Label>Protocol</Form.Label>
              <Form.Control
                as="select"
                name="protocol"
                value={newRule.rule.protocol}
                onChange={(e) =>
                  setNewRule({
                    ...newRule,
                    rule: { ...newRule.rule, protocol: e.target.value },
                  })
                }
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
                onChange={(e) =>
                  setNewRule({
                    ...newRule,
                    rule: { ...newRule.rule, source: e.target.value },
                  })
                }
              />
            </Form.Group>
            <Form.Group controlId="destination">
              <Form.Label>Destination</Form.Label>
              <Form.Control
                type="text"
                name="destination"
                value={newRule.rule.destination}
                onChange={(e) =>
                  setNewRule({
                    ...newRule,
                    rule: { ...newRule.rule, destination: e.target.value },
                  })
                }
              />
            </Form.Group>
            <Button type="submit">Add Rule</Button>
          </Form>
        </Card.Body>
      </Card>

      <Card className="my-4">
        <Card.Body>
          <h3>Clear Forwarding Rules</h3>
          <Button variant="danger" onClick={handleClear}>
            Clear Rules
          </Button>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default ForwardingRulesPage;
