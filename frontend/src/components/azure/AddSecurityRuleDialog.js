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
  container,
}) => {
  const [securityRules, setSecurityRules] = useState([]);
  const [loadingSecurityRules, setLoadingSecurityRules] = useState(false);

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
  }, []);

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
                </tr>
              </thead>
              <tbody>
                {/* Display firstly inbound rules */}
                <tr>
                  <td colSpan="5" style={{ textAlign: "center", fontWeight: "bold" }}>
                    Inbound
                  </td>
                </tr>
                {securityRules
                  .filter((rule) => rule.direction === "Inbound")
                  .map((rule) => (
                    <tr key={rule.name}>
                      <td>{rule.name}</td>
                      <td>{rule.priority}</td>
                      <td>{rule.source_address_prefix + ":" + rule.source_port_range}</td>
                      <td>{rule.destination_address_prefix + ":" + rule.destination_port_range}</td>
                      <td>{rule.protocol}</td>
                    </tr>
                  ))}
                {/* Display secondly outbound rules */}
                <tr>
                  <td colSpan="5" style={{ textAlign: "center", fontWeight: "bold" }}>
                    Outbound
                  </td>
                </tr>
                {securityRules
                  .filter((rule) => rule.direction === "Outbound")
                  .map((rule) => (
                    <tr key={rule.name}>
                      <td>{rule.name}</td>
                      <td>{rule.priority}</td>
                      <td>{rule.source_address_prefix + ":" + rule.source_port_range}</td>
                      <td>{rule.destination_address_prefix + ":" + rule.destination_port_range}</td>
                      <td>{rule.protocol}</td>
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
      </DialogContent>
      <DialogActions>
        <Button
          onClick={() => setOpenAddSecurityRuleDialog(false)}
          color="primary"
        >
          Cancel
        </Button>
        <Button
          onClick={() => setOpenAddSecurityRuleDialog(false)}
          color="primary"
        >
          Add
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AddSecurityRuleDialog;
