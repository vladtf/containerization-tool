import { IconButton } from "@mui/material";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import axios from "axios";
import { useEffect, useState } from "react";
import { Button, Spinner, Table } from "react-bootstrap";
import { IoCloseOutline } from "react-icons/io5";
import { toast } from "react-toastify";
import { PYTHON_BACKEND_URL } from "../../config/BackendConfiguration";

const AddSecurityRuleDialog = ({
  openAddSecurityRuleDialog,
  setOpenAddSecurityRuleDialog,
}) => {
  const [securityRules, setSecurityRules] = useState([]);
  const [loadingSecurityRules, setLoadingSecurityRules] = useState(false);

  const [name, setName] = useState("");
  const [priority, setPriority] = useState("");
  const [direction, setDirection] = useState("Inbound");
  const [source, setSource] = useState("");
  const [destination, setDestination] = useState("");
  const [protocol, setProtocol] = useState("*");
  const [access, setAccess] = useState("Allow");
  const [description, setDescription] = useState("");
  const [sourcePortRange, setSourcePortRange] = useState("");
  const [destinationPortRange, setDestinationPortRange] = useState("");

  const [loadingAddSecurityRule, setLoadingAddSecurityRule] = useState(false);

  useEffect(() => {
    setLoadingSecurityRules(true);
    axios
      .get(`${PYTHON_BACKEND_URL}/azure/security-rules`)
      .then((response) => {
        setSecurityRules(response.data);
      })
      .catch((error) => {
        toast.error(error.message);
      })
      .finally(() => {
        setLoadingSecurityRules(false);
      });
  }, [openAddSecurityRuleDialog, setOpenAddSecurityRuleDialog]);

  const handleAddSecurityRule = (e) => {
    e.preventDefault();

    setLoadingAddSecurityRule(true);
    axios
      .post(`${PYTHON_BACKEND_URL}/azure/security-rules`, {
        name,
        priority,
        direction,
        source,
        destination,
        protocol,
        access,
        description,
        sourcePortRange,
        destinationPortRange,
      })
      .then((response) => {
        toast.success(response.data);
        setOpenAddSecurityRuleDialog(false);
      })
      .catch((error) => {
        console.log(error);
        toast.error(error.response.data || error.message);
      })
      .finally(() => {
        setLoadingAddSecurityRule(false);
      });
  };

  return (
    <Dialog
      open={openAddSecurityRuleDialog}
      onClose={() => setOpenAddSecurityRuleDialog(false)}
      fullScreen
    >
      <DialogTitle>
        Add Security Rule
        <IconButton
          edge="end"
          color="inherit"
          onClick={() => setOpenAddSecurityRuleDialog(false)}
          aria-label="close"
          style={{ position: "absolute", right: "2rem", top: "1rem" }}
        >
          <IoCloseOutline />
        </IconButton>
      </DialogTitle>

      <DialogContent>
        {/* Display existing security rules */}
        {loadingSecurityRules ? (
          <div>
            Loading security rules...{" "}
            <Spinner animation="border" variant="success" size="sm" />
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <Table striped bordered hover responsive>
              <thead>
                <tr>
                  <th>Rule Name</th>
                  <th>Priority</th>
                  <th>Source</th>
                  <th>Destination</th>
                  <th>Protocol</th>
                  <th>Access</th>
                </tr>
              </thead>
              <tbody>
                {/* Display firstly inbound rules */}
                <tr>
                  <td
                    colSpan="6"
                    style={{ textAlign: "center", fontWeight: "bold" }}
                  >
                    Inbound
                  </td>
                </tr>
                {securityRules
                  .filter((rule) => rule.direction === "Inbound")
                  .map((rule) => (
                    <tr key={rule.name}>
                      <td>{rule.name}</td>
                      <td>{rule.priority}</td>
                      <td>
                        {rule.source_address_prefix +
                          ":" +
                          rule.source_port_range}
                      </td>
                      <td>
                        {rule.destination_address_prefix +
                          ":" +
                          rule.destination_port_range}
                      </td>
                      <td>{rule.protocol}</td>
                      <td>{rule.access}</td>
                    </tr>
                  ))}
                {/* Display secondly outbound rules */}
                <tr>
                  <td
                    colSpan="6"
                    style={{ textAlign: "center", fontWeight: "bold" }}
                  >
                    Outbound
                  </td>
                </tr>
                {securityRules
                  .filter((rule) => rule.direction === "Outbound")
                  .map((rule) => (
                    <tr key={rule.name}>
                      <td>{rule.name}</td>
                      <td>{rule.priority}</td>
                      <td>
                        {rule.source_address_prefix +
                          ":" +
                          rule.source_port_range}
                      </td>
                      <td>
                        {rule.destination_address_prefix +
                          ":" +
                          rule.destination_port_range}
                      </td>
                      <td>{rule.protocol}</td>
                      <td>{rule.access}</td>
                    </tr>
                  ))}
              </tbody>
            </Table>
          </div>
        )}
      </DialogContent>

      <DialogContent>
        <DialogContentText>
          To add a new security rule, please enter the following information
          here.
        </DialogContentText>
        {/* Form to add a new security rule */}
        <form>
          <div className="mb-3">
            <label htmlFor="name" className="form-label">
              Rule Name
            </label>
            <input
              type="text"
              className="form-control"
              id="name"
              placeholder="Enter rule name"
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="mb-3">
            <label htmlFor="priority" className="form-label">
              Priority
            </label>
            <input
              type="number"
              className="form-control"
              id="priority"
              placeholder="Enter priority"
              onChange={(e) => setPriority(e.target.value)}
            />
          </div>
          <div className="mb-3">
            <label htmlFor="direction" className="form-label">
              Direction
            </label>
            <select
              className="form-select"
              id="direction"
              onChange={(e) => setDirection(e.target.value)}
            >
              <option value="Inbound">Inbound</option>
              <option value="Outbound">Outbound</option>
            </select>
          </div>
          <div className="mb-3">
            <label htmlFor="source" className="form-label">
              Source
            </label>
            <input
              type="text"
              className="form-control"
              id="source"
              placeholder="Enter source"
              onChange={(e) => setSource(e.target.value)}
            />
          </div>
          <div className="mb-3">
            <label htmlFor="destination" className="form-label">
              Destination
            </label>
            <input
              type="text"
              className="form-control"
              id="destination"
              placeholder="Enter destination"
              onChange={(e) => setDestination(e.target.value)}
            />
          </div>
          <div className="mb-3">
            <label htmlFor="protocol" className="form-label">
              Protocol
            </label>
            <select
              className="form-select"
              id="protocol"
              onChange={(e) => setProtocol(e.target.value)}
            >
              <option value="*">ANY</option>
              <option value="TCP">TCP</option>
              <option value="UDP">UDP</option>
              <option value="ICMP">ICMP</option>
            </select>
          </div>
          <div className="mb-3">
            <label htmlFor="source_port_range" className="form-label">
              Source Port Range
            </label>
            <input
              type="text"
              className="form-control"
              id="source_port_range"
              placeholder="Enter source port range"
              onChange={(e) => setSourcePortRange(e.target.value)}
            />
          </div>
          <div className="mb-3">
            <label htmlFor="destination_port_range" className="form-label">
              Destination Port Range
            </label>
            <input
              type="text"
              className="form-control"
              id="destination_port_range"
              placeholder="Enter destination port range"
              onChange={(e) => setDestinationPortRange(e.target.value)}
            />
          </div>
          <div className="mb-3">
            <label htmlFor="access" className="form-label">
              Access
            </label>
            <select
              className="form-select"
              id="access"
              onChange={(e) => setAccess(e.target.value)}
            >
              <option value="Allow">Allow</option>
              <option value="Deny">Deny</option>
            </select>
          </div>
          <div className="mb-3">
            <label htmlFor="description" className="form-label">
              Description
            </label>
            <textarea
              className="form-control"
              id="description"
              rows="3"
              placeholder="Enter description"
              onChange={(e) => setDescription(e.target.value)}
            ></textarea>
          </div>
        </form>
      </DialogContent>
      <DialogActions>
        <Button
          onClick={() => setOpenAddSecurityRuleDialog(false)}
          variant="danger"
        >
          Cancel
        </Button>
        <Button
          onClick={handleAddSecurityRule}
          variant="success"
          disabled={loadingAddSecurityRule}
        >
          Add Security Rule
          {loadingAddSecurityRule && (
            <>
              {" "}
              <Spinner animation="border" size="sm" />
            </>
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AddSecurityRuleDialog;
