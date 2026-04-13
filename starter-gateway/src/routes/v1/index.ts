import { Router } from "express";
import { healthRouter } from "./health";

export const v1Router = Router();

v1Router.use("/health", healthRouter);

// Mount additional v1 route modules here:
// v1Router.use("/users", usersRouter);
// v1Router.use("/orders", ordersRouter);
