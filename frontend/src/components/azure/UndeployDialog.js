import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import axios from "axios";
import { Button } from "react-bootstrap";
import { toast } from "react-toastify";
import { PYTHON_BACKEND_URL } from "../../config/BackendConfiguration";

const UndeployDialog = ({
  openUndeployContainerDialog,
  setOpenUndeployContainerDialog,
  container,
  fetchContainers,
  setLoading,
}) => {
  const handleUndeployContainer = async (container) => {
    const containerId = container.id;

    console.log("Undeploying container:", containerId);

    setLoading(true);
    axios
      .delete(`${PYTHON_BACKEND_URL}/azure/deploy/${containerId}`)
      .then((response) => {
        console.log(response);
        toast.success("Container undeployed successfully");
        fetchContainers();
      })
      .catch((error) => {
        console.error(error);
        toast.error("Failed to undeploy container: " + error.response.data);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <Dialog
      open={openUndeployContainerDialog}
      onClose={() => setOpenUndeployContainerDialog(false)}
    >
      <DialogTitle>Undeploy Container</DialogTitle>
      <DialogContent>
        <DialogContentText>
          Are you sure you want to undeploy this container:
          {container && container.name}?
        </DialogContentText>
      </DialogContent>

      <DialogActions>
        <Button
          variant="primary"
          onClick={() => setOpenUndeployContainerDialog(false)}
        >
          Cancel
        </Button>
        <Button
          variant="outline-danger"
          onClick={() => {
            setOpenUndeployContainerDialog(false);
            handleUndeployContainer(container);
          }}
        >
          Undeploy
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default UndeployDialog;
