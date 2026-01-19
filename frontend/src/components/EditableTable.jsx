import React, { useState } from 'react';
import { Form, Input, Table, Tooltip } from 'antd';

const EditableCell = ({
  editing,
  dataIndex,
  title,
  inputType,
  record,
  index,
  children,
  ...restProps
}) => {
  const inputNode = <Input />;
  return (
    <td {...restProps}>
      {editing ? (
        <Form.Item
          name={dataIndex}
          style={{ margin: 0 }}
          rules={[{ required: false }]}
        >
          {inputNode}
        </Form.Item>
      ) : (
        children
      )}
    </td>
  );
};

const EditableTable = ({ columns, dataSource, confMatrix, onChange }) => {
  const [form] = Form.useForm();
  const [editingKey, setEditingKey] = useState('');

  const isEditing = (record) => record.key === editingKey;

  const edit = (record) => {
    form.setFieldsValue({ ...record });
    setEditingKey(record.key);
  };

  const cancel = () => {
    setEditingKey('');
  };

  const save = async (key) => {
    try {
      const row = await form.validateFields();
      const newData = [...dataSource];
      const index = newData.findIndex((item) => key === item.key);
      if (index > -1) {
        const item = newData[index];
        newData.splice(index, 1, { ...item, ...row });
        onChange(newData);
        setEditingKey('');
      }
    } catch (errInfo) {
      console.warn('Save failed:', errInfo);
    }
  };

  const mergedColumns = columns.map((col, colIndex) => ({
    ...col,
    onCell: (record) => ({
      record,
      inputType: 'text',
      dataIndex: col.dataIndex,
      title: col.title,
      editing: isEditing(record)
    }),
    render: (text, record, rowIndex) => {
      const conf = confMatrix?.[rowIndex]?.[colIndex];
      const content = text ?? '';
      const cellClass = conf !== undefined && conf !== -1 && conf < 60 ? 'conf-low' : '';
      return (
        <Tooltip title={conf !== undefined && conf !== -1 ? `置信度: ${conf}` : ''}>
          <div className={cellClass} style={{ padding: '4px 0' }}>{content}</div>
        </Tooltip>
      );
    }
  }));

  return (
    <Form form={form} component={false}>
      <Table
        components={{ body: { cell: EditableCell } }}
        bordered
        dataSource={dataSource}
        columns={mergedColumns}
        rowClassName="editable-row"
        pagination={{ pageSize: 8 }}
        onRow={(record) => ({
          onClick: () => (isEditing(record) ? null : edit(record)),
          onDoubleClick: () => edit(record)
        })}
      />
      {editingKey && (
        <div style={{ marginTop: 8 }}>
          <a onClick={() => save(editingKey)} style={{ marginRight: 8 }}>保存行</a>
          <a onClick={cancel}>取消</a>
        </div>
      )}
    </Form>
  );
};

export default EditableTable;
