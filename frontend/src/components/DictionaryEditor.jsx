import React, { useState, useEffect } from "react";
import { getDefaultDictionary } from "../api";

const DictionaryEditor = ({ onChange }) => {
  const [dictionaryItems, setDictionaryItems] = useState([]);
  const [newItem, setNewItem] = useState("");
  const [useDefaultDict, setUseDefaultDict] = useState(true);
  const [showAll, setShowAll] = useState(false);

  // Load default dictionary when component mounts
  useEffect(() => {
    if (useDefaultDict) {
      setDictionaryItems(getDefaultDictionary());
    }
  }, [useDefaultDict]);

  // Add item
  const handleAddItem = () => {
    if (newItem.trim()) {
      // Check if path has / at the end
      const formattedItem = newItem.trim().endsWith("/")
        ? newItem.trim()
        : `${newItem.trim()}/`;

      if (!dictionaryItems.includes(formattedItem)) {
        const updatedItems = [...dictionaryItems, formattedItem];
        setDictionaryItems(updatedItems);

        // Notify parent component of changes
        const addOperation = {
          type: "add",
          paths: [formattedItem],
        };

        onChange({
          operations: [addOperation],
          useDefault: useDefaultDict,
        });

        setNewItem("");
      } else {
        alert("This item already exists in the list.");
      }
    }
  };

  // Remove item
  const handleRemoveItem = (item) => {
    const updatedItems = dictionaryItems.filter((i) => i !== item);
    setDictionaryItems(updatedItems);

    // Notify parent component of changes
    const removeOperation = {
      type: "remove",
      paths: [item],
    };

    onChange({
      operations: [removeOperation],
      useDefault: useDefaultDict,
    });
  };

  // Toggle default dictionary usage
  const handleDefaultToggle = () => {
    const newValue = !useDefaultDict;
    setUseDefaultDict(newValue);

    if (newValue) {
      // Switch to using default dictionary
      setDictionaryItems(getDefaultDictionary());
    } else {
      // Stop using default dictionary, use only custom list
      setDictionaryItems([]);
    }

    // Notify parent component of changes
    onChange({
      operations: [],
      useDefault: newValue,
    });
  };

  // Calculate number of items to display
  const visibleItems = showAll ? dictionaryItems : dictionaryItems.slice(0, 10);

  return (
    <div className="dictionary-editor">
      <h3 className="form-label">Dictionary Settings</h3>
      <p className="form-hint">Manage the list of directory paths to scan.</p>

      <div className="form-group checkbox-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={useDefaultDict}
            onChange={handleDefaultToggle}
            className="form-checkbox"
          />
          <span>Use Default Dictionary (Recommended)</span>
        </label>
      </div>

      <div className="dictionary-input-group">
        <input
          type="text"
          value={newItem}
          onChange={(e) => setNewItem(e.target.value)}
          placeholder="Directory path to add (e.g., admin/)"
          className="form-control"
          style={{ flex: 1 }}
        />
        <button
          type="button"
          onClick={handleAddItem}
          className="btn btn-secondary"
          disabled={!newItem.trim()}
        >
          Add
        </button>
      </div>

      <div className="dictionary-list">
        <p className="form-hint">
          Current dictionary items: {dictionaryItems.length}
          {dictionaryItems.length > 10 && !showAll && (
            <button
              type="button"
              onClick={() => setShowAll(true)}
              className="btn-link"
            >
              Show All
            </button>
          )}
          {showAll && (
            <button
              type="button"
              onClick={() => setShowAll(false)}
              className="btn-link"
            >
              Collapse
            </button>
          )}
        </p>

        <div className="dictionary-items">
          {visibleItems.length > 0 ? (
            visibleItems.map((item, index) => (
              <div key={index} className="dictionary-item">
                <span>{item}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveItem(item)}
                  className="btn-close"
                  aria-label="Remove"
                >
                  ×
                </button>
              </div>
            ))
          ) : (
            <p className="empty-message">Dictionary items are empty.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default DictionaryEditor;
