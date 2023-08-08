import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import axios from "axios";
import { Button } from "react-bootstrap";
import { toast } from "react-toastify";
import { PYTHON_BACKEND_URL } from "../../config/BackendConfiguration";

const DeleteInstanceDialog = ({
  openDeleteInstanceDialog,
  setOpenDeleteInstanceDialog,
  selectedInstance,
  fetchAzureContainerInstances,
}) => {
  const handleDeleteContainerInstance = (instanceName) => {
    console.log("Deleting instance:", instanceName);
    toast.success("Deleting instance: " + instanceName);

    axios
      .delete(`${PYTHON_BACKEND_URL}/azure/instances/${instanceName}`)
      .then((response) => {
        console.log(response);
        toast.success("Instance '" + instanceName + "' deleted successfully");
        fetchAzureContainerInstances();
      })
      .catch((error) => {
        console.error(error);
        toast.error("Failed to delete instance: " + error.response.data);
      });
  };

  return (
    <Dialog
      open={openDeleteInstanceDialog}
      onClose={() => setOpenDeleteInstanceDialog(false)}
    >
      <DialogTitle>Delete Instance</DialogTitle>
      <DialogContent>
        <DialogContentText>
          Are you sure you want to delete this instance: {selectedInstance}?
        </DialogContentText>
      </DialogContent>

      <DialogActions>
        <Button
          variant="primary"
          onClick={() => setOpenDeleteInstanceDialog(false)}
        >
          Cancel
        </Button>
        <Button
          variant="outline-danger"
          onClick={() => {
            setOpenDeleteInstanceDialog(false);
            handleDeleteContainerInstance(selectedInstance);
          }}
        >
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DeleteInstanceDialog;
