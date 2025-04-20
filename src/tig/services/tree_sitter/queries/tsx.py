tsx_query = """
(function_signature
  name: (identifier) @name.definition.function) @definition.function

(method_signature
  name: (property_identifier) @name.definition.method) @definition.method

(abstract_method_signature
  name: (property_identifier) @name.definition.method) @definition.method

(abstract_class_declaration
  name: (type_identifier) @name.definition.class) @definition.class

(module
  name: (identifier) @name.definition.module) @definition.module

(function_declaration
  name: (identifier) @name.definition.function) @definition.function

(method_definition
  name: (property_identifier) @name.definition.method) @definition.method

(class_declaration
  name: (type_identifier) @name.definition.class) @definition.class

(call_expression
  function: (identifier) @func_name
  arguments: (arguments
    (string) @name
    [(arrow_function) (function_expression)]) @definition.test)
  (#match? @func_name "^(describe|test|it)$")

(assignment_expression
  left: (member_expression
    object: (identifier) @obj
    property: (property_identifier) @prop)
  right: [(arrow_function) (function_expression)]) @definition.test
  (#eq? @obj "exports")
  (#eq? @prop "test")
(arrow_function) @definition.lambda

; Switch statements and case clauses
(switch_statement) @definition.switch

; Individual case clauses with their blocks
(switch_case) @definition.case

; Default clause
(switch_default) @definition.default

; Enum declarations
(enum_declaration
  name: (identifier) @name.definition.enum) @definition.enum

; Decorator definitions with decorated class
(export_statement
  decorator: (decorator
    (call_expression
      function: (identifier) @name.definition.decorator))
  declaration: (class_declaration
    name: (type_identifier) @name.definition.decorated_class)) @definition.decorated_class

; Explicitly capture class name in decorated class
(class_declaration
  name: (type_identifier) @name.definition.class) @definition.class

; Namespace declarations
(internal_module
  name: (identifier) @name.definition.namespace) @definition.namespace

; Interface declarations with generic type parameters and constraints
(interface_declaration
  name: (type_identifier) @name.definition.interface
  type_parameters: (type_parameters)?) @definition.interface

; Type alias declarations with generic type parameters and constraints
(type_alias_declaration
  name: (type_identifier) @name.definition.type
  type_parameters: (type_parameters)?) @definition.type

; Utility Types
(type_alias_declaration
  name: (type_identifier) @name.definition.utility_type) @definition.utility_type

; Class Members and Properties
(public_field_definition
  name: (property_identifier) @name.definition.property) @definition.property

; Constructor
(method_definition
  name: (property_identifier) @name.definition.constructor
  (#eq? @name.definition.constructor "constructor")) @definition.constructor

; Getter/Setter Methods
(method_definition
  name: (property_identifier) @name.definition.accessor) @definition.accessor

; Async Functions
(function_declaration
  name: (identifier) @name.definition.async_function) @definition.async_function

; Async Arrow Functions
(variable_declaration
  (variable_declarator
    name: (identifier) @name.definition.async_arrow
    value: (arrow_function))) @definition.async_arrow

; React Component Definitions
; Function Components
(function_declaration
  name: (identifier) @name.definition.component) @definition.component

; Arrow Function Components
(variable_declaration
  (variable_declarator
    name: (identifier) @name.definition.component
    value: [(arrow_function) (function_expression)])) @definition.component

; Class Components
(class_declaration
  name: (type_identifier) @name.definition.component
  (class_heritage
    (extends_clause
      (member_expression) @base))) @definition.component

; Higher Order Components
(variable_declaration
  (variable_declarator
    name: (identifier) @name.definition.component
    value: (call_expression
      function: (identifier) @hoc))) @definition.component
  (#match? @hoc "^with[A-Z]")

; Capture all named definitions (component or not)
(variable_declaration
  (variable_declarator
    name: (identifier) @name.definition
    value: [
      (call_expression) @value
      (arrow_function) @value
    ])) @definition.component

; Capture all exported component declarations, including React component wrappers
(export_statement
  (variable_declaration
    (variable_declarator
      name: (identifier) @name.definition.component
      value: [
        (call_expression) @value
        (arrow_function) @value
      ]))) @definition.component

; Capture React component name inside wrapped components
(call_expression
  function: (_)
  arguments: (arguments
    (arrow_function))) @definition.wrapped_component

; HOC definitions - capture both the HOC name and definition
(variable_declaration
  (variable_declarator
    name: (identifier) @name.definition.hoc
    value: (arrow_function
      parameters: (formal_parameters)))) @definition.hoc

; Type definitions (to include interfaces and types)
(type_alias_declaration
  name: (type_identifier) @name.definition.type) @definition.type

(interface_declaration
  name: (type_identifier) @name.definition.interface) @definition.interface

; Enhanced Components
(variable_declaration
  (variable_declarator
    name: (identifier) @name.definition.component
    value: (call_expression))) @definition.component

; Types and Interfaces
(interface_declaration
  name: (type_identifier) @name.definition.interface) @definition.interface

(type_alias_declaration
  name: (type_identifier) @name.definition.type) @definition.type

; JSX Component Usage - Capture all components in JSX
(jsx_element
  open_tag: (jsx_opening_element
    name: [(identifier) @component (member_expression) @component])) @definition.component
  (#match? @component "^[A-Z]")

(jsx_self_closing_element
  name: [(identifier) @component (member_expression) @component]) @definition.component
  (#match? @component "^[A-Z]")

; Capture all identifiers in JSX expressions that start with capital letters
(jsx_expression
  (identifier) @jsx_component) @definition.jsx_component
  (#match? @jsx_component "^[A-Z]")

; Capture all member expressions in JSX
(member_expression
  object: (identifier) @object
  property: (property_identifier) @property) @definition.member_component
  (#match? @object "^[A-Z]")

; Capture components in conditional expressions
(ternary_expression
  consequence: (parenthesized_expression
    (jsx_element
      open_tag: (jsx_opening_element
        name: (identifier) @component)))) @definition.conditional_component
  (#match? @component "^[A-Z]")

(ternary_expression
  alternative: (jsx_self_closing_element
    name: (identifier) @component)) @definition.conditional_component
  (#match? @component "^[A-Z]")

; Enhanced TypeScript Support - React-specific patterns only
; Method Definitions specific to React components
(method_definition
  name: (property_identifier) @name.definition.method) @definition.method

; React Hooks
(variable_declaration
  (variable_declarator
    name: (array_pattern) @name.definition.hook
    value: (call_expression
      function: (identifier) @hook_name))) @definition.hook
  (#match? @hook_name "^use[A-Z]")

; Custom Hooks
(function_declaration
  name: (identifier) @name.definition.custom_hook) @definition.custom_hook
  (#match? @name.definition.custom_hook "^use[A-Z]")

; Context Providers and Consumers
(variable_declaration
  (variable_declarator
    name: (identifier) @name.definition.context
    value: (member_expression))) @definition.context

; React-specific decorators
(decorator) @definition.decorator
"""
