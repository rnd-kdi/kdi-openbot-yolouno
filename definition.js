// Khối kiểm tra có target data không
Blockly.Blocks['has_target_data'] = {
  init: function () {
    this.jsonInit({
      type: "has_target_data",
      message0: "Có target data không",
      output: "Boolean",
      colour: "#cb2026",
      tooltip: "Kiểm tra xem có dữ liệu target từ OpenBot hay không",
      helpUrl: ""
    });
  }
};

Blockly.Python['has_target_data'] = function(block) {
  Blockly.Python.definitions_['import_openbot_parser'] = 'from yolouno_phone import OpenBotParser';
  Blockly.Python.definitions_['create_openbot_parser'] = 'parser = OpenBotParser()';
  
  var code = 'parser.is_target_available()';
  return [code, Blockly.Python.ORDER_ATOMIC];
};

// Khối lấy thông tin target
Blockly.Blocks['get_target_info'] = {
  init: function () {
    this.jsonInit({
      type: "get_target_info",
      message0: "Lấy %1 của vật thể",
      args0: [
        {
          type: "field_dropdown",
          name: "PROPERTY",
          options: [
            ["x", "x"],
            ["y", "y"],
            ["w", "w"],
            ["h", "h"]
          ]
        }
      ],
      output: "Number",
      colour: "#cb2026",
      tooltip: "x,y là tọa độ trung tâm, w là chiều rộng, h là chiều cao",
      helpUrl: ""
    });
  }
};

Blockly.Python['get_target_info'] = function(block) {
  var property = block.getFieldValue('PROPERTY');
  
  Blockly.Python.definitions_['import_openbot_parser'] = 'from yolouno_phone import OpenBotParser';
  Blockly.Python.definitions_['create_openbot_parser'] = 'parser = OpenBotParser()';
  
  var code = 'parser.get_target_' + property + '()';
  return [code, Blockly.Python.ORDER_ATOMIC];
};

// Khối đọc dữ liệu từ stdin
Blockly.Blocks['read_openbot_data'] = {
 init: function () {
   this.jsonInit({
     type: "read_openbot_data",
     message0: "Đọc dữ liệu OpenBot",
     previousStatement: null,
     nextStatement: null,
     colour: "#cb2026",
     tooltip: "Đọc dữ liệu từ stdin và xử lý tin nhắn OpenBot",
     helpUrl: ""
   });
 }
};

Blockly.Python['read_openbot_data'] = function(block) {
 Blockly.Python.definitions_['import_openbot_parser'] = 'from yolouno_phone import OpenBotParser';
 Blockly.Python.definitions_['create_openbot_parser'] = 'parser = OpenBotParser()';
 
 var code = 'parser.read_stdin()\n';
 return code;
};