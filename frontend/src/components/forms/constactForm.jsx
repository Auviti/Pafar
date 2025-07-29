// components/ContactForm.jsx
import React, { useState } from "react";

export default function ContactForm() {
  const [formState, setFormState] = useState({
    name: "",
    email: "",
    message: "",
  });

  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState("init");
  const [responseMessage, setResponseMessage] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormState((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: "" }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("validating");

    const newErrors = validateForm(formState);
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      setStatus("validation_failed");
      return;
    }

    setStatus("submitting");

    try {
      const formData = new FormData();
      Object.entries(formState).forEach(([key, value]) => {
        formData.append(key, value);
      });

      const res = await fetch("https://your-api-endpoint", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (data.status === "mail_sent") {
        setFormState({ name: "", email: "", message: "" });
        setStatus("sent");
      } else {
        setStatus("failed");
      }

      setResponseMessage(data.message || "Form submission complete.");
    } catch (err) {
      console.error(err);
      setStatus("failed");
      setResponseMessage("Something went wrong.");
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate data-status={status}>
      <div>
        <label>
          Name
          <input
            name="name"
            value={formState.name}
            onChange={handleChange}
            aria-invalid={!!errors.name}
          />
          {errors.name && <span className="wpcf7-not-valid-tip">{errors.name}</span>}
        </label>
      </div>

      <div>
        <label>
          Email
          <input
            name="email"
            value={formState.email}
            onChange={handleChange}
            aria-invalid={!!errors.email}
          />
          {errors.email && <span className="wpcf7-not-valid-tip">{errors.email}</span>}
        </label>
      </div>

      <div>
        <label>
          Message
          <textarea
            name="message"
            value={formState.message}
            onChange={handleChange}
            aria-invalid={!!errors.message}
          />
          {errors.message && <span className="wpcf7-not-valid-tip">{errors.message}</span>}
        </label>
      </div>

      <button type="submit" disabled={status === "submitting"}>
        {status === "submitting" ? "Submitting..." : "Send"}
      </button>

      {responseMessage && (
        <div className="wpcf7-response-output" role="status">
          {responseMessage}
        </div>
      )}
    </form>
  );
}

function validateForm({ name, email, message }) {
  const errors = {};
  if (!name.trim()) errors.name = "Name is required.";
  if (!email.trim()) {
    errors.email = "Email is required.";
  } else if (!/^\S+@\S+\.\S+$/.test(email)) {
    errors.email = "Email is invalid.";
  }
  if (!message.trim()) errors.message = "Message is required.";
  return errors;
}
