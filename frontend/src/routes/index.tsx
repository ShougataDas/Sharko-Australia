import { createBrowserRouter } from "react-router-dom";

import App from "../App";
import { SensorDiagram } from "../components/Sensor";

const routes = createBrowserRouter([
  {
    path: "/",
    element: <App />,
  },
  {
    path: "/tag",
    element: <SensorDiagram />,
  },
  {
    path: "*",
    element: <h3>Not Found</h3>,
  },
]);

export default routes;
