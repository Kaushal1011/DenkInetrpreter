###############################################################################
#                                                                             #
#  SYMBOLS, TABLES, SEMANTIC ANALYSIS                                         #
#                                                                             #
###############################################################################
from base import _SHOULD_LOG_SCOPE
from base import _SHOULD_LOG_STACK
from astvisitor import NodeVisitor
from base import ErrorCode
from base import SemanticError
from lex import TokenType

class Symbol:
    def __init__(self, name, type=None):
        self.name = name
        self.type = type


class VarSymbol(Symbol):
    def __init__(self, name, type):
        super().__init__(name, type)

    def __str__(self):
        return "<{class_name}(name='{name}', type='{type}')>".format(
            class_name=self.__class__.__name__,
            name=self.name,
            type=self.type,
        )

    __repr__ = __str__


class BuiltinTypeSymbol(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<{class_name}(name='{name}')>".format(
            class_name=self.__class__.__name__,
            name=self.name,
        )


class ProcedureSymbol(Symbol):
    def __init__(self, name, params=None):
        super().__init__(name)
        # a list of formal parameters
        self.params = params if params is not None else []

    def __str__(self):
        return '<{class_name}(name={name}, parameters={params})>'.format(
            class_name=self.__class__.__name__,
            name=self.name,
            params=self.params,
        )

    __repr__ = __str__


class ScopedSymbolTable:
    hasReturnStatement=False
    def __init__(self, scope_name,scopeType, scope_level, enclosing_scope=None):
        self._symbols = {}
        self.scope_name = scope_name
        self.scopeType=TokenType
        self.scope_level = scope_level
        self.enclosing_scope = enclosing_scope
        self._init_builtins()

    def _init_builtins(self):
        self.insert(BuiltinTypeSymbol('INTEGER'))
        self.insert(BuiltinTypeSymbol('REAL'))

    def __str__(self):
        h1 = 'SCOPE (SCOPED SYMBOL TABLE)'
        lines = ['\n', h1, '=' * len(h1)]
        for header_name, header_value in (
            ('Scope name', self.scope_name),
            ('Scope level', self.scope_level),
            ('Enclosing scope',
             self.enclosing_scope.scope_name if self.enclosing_scope else None
            )
        ):
            lines.append('%-15s: %s' % (header_name, header_value))
        h2 = 'Scope (Scoped symbol table) contents'
        lines.extend([h2, '-' * len(h2)])
        lines.extend(
            ('%7s: %r' % (key, value))
            for key, value in self._symbols.items()
        )
        lines.append('\n')
        s = '\n'.join(lines)
        return s

    __repr__ = __str__

    def log(self, msg):
        if _SHOULD_LOG_SCOPE:
            print(msg)

    def insert(self, symbol):
        self.log(f'Insert: {symbol.name}')
        self._symbols[symbol.name] = symbol

    def lookup(self, name, current_scope_only=False):
        self.log(f'Lookup: {name}. (Scope name: {self.scope_name})')
        # 'symbol' is either an instance of the Symbol class or None
        symbol = self._symbols.get(name)

        if symbol is not None:
            return symbol

        if current_scope_only:
            return None

        # recursively go up the chain and lookup the name
        if self.enclosing_scope is not None:
            return self.enclosing_scope.lookup(name)


class SemanticAnalyzer(NodeVisitor):
    def __init__(self,scope):
        self.current_scope = ScopedSymbolTable("initial",TokenType.PROGRAM,1)
        _SHOULD_LOG_SCOPE=scope

    def log(self, msg):
        if _SHOULD_LOG_SCOPE:
            print(msg)

    def error(self, error_code, token):
        raise SemanticError(
            error_code=error_code,
            token=token,
            message=f'{error_code.value} -> {token}',
        )

    def visit_Block(self, node):
        for declaration in node.declarations:
            self.visit(declaration)
        self.visit(node.compound_statement)

    def visit_Program(self, node):
        self.log('ENTER scope: global')
        global_scope = ScopedSymbolTable(
            scope_name='global',
            scopeType=TokenType.PROGRAM,
            scope_level=1,
            enclosing_scope=self.current_scope,  # None
        )
        self.current_scope = global_scope

        # visit subtree
        self.visit(node.block)

        self.log(global_scope)

        self.current_scope = self.current_scope.enclosing_scope
        self.log('LEAVE scope: global')

    def visit_Compound(self, node):
        for child in node.children:
            self.visit(child)

    def visit_NoOp(self, node):
        pass

    def visit_Type(self,node):
        pass

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_ProcedureDecl(self, node):
        proc_name = node.procName
        proc_symbol = ProcedureSymbol(proc_name)
        self.current_scope.insert(proc_symbol)

        self.log(f'ENTER scope: {proc_name}')
        # Scope for parameters and local variables
        procedure_scope = ScopedSymbolTable(
            scope_name=proc_name,
            scopeType=TokenType.PROCEDURE,
            scope_level=self.current_scope.scope_level + 1,
            enclosing_scope=self.current_scope
        )
        self.current_scope = procedure_scope

        # Insert parameters into the procedure scope
        for param in node.params:
            param_type = self.current_scope.lookup(param.type_node.value)
            param_name = param.var_node.value
            var_symbol = VarSymbol(param_name, param_type)
            self.current_scope.insert(var_symbol)
            proc_symbol.params.append(var_symbol)

        self.visit(node.blockNode)

        self.log(procedure_scope)

        self.current_scope = self.current_scope.enclosing_scope
        self.log(f'LEAVE scope: {proc_name}')

    def visit_FunctionDecl(self,node):
        funcName=node.funcName
        funcSymbol=ProcedureSymbol(funcName)
        self.current_scope.insert(funcSymbol)
        self.log("Enter Scope:{}".format(funcName))
        procedureScope=ScopedSymbolTable(
            funcName,
            TokenType.FUNCTION,
            self.current_scope.scope_level + 1,
            self.current_scope
            )
        self.current_scope=procedureScope
        for param in node.params:
            paramType=self.current_scope.lookup(param.typeNode.value)
            paramName=param.var_node.value
            varSymbol=VarSymbol(paramName,paramType)
            self.current_scope.insert(varSymbol)
            funcSymbol.params.append(varSymbol)

        self.visit_Type(node.returnType)
        self.visit(node.blockNode)
        self.log("{}".format(procedureScope))
        if procedureScope.hasReturnStatement==False:
            self.error(
            ErrorCode.MISSING_RETURN,
            node.token
        )
        self.current_scope=self.current_scope.enclosingScope
        self.log('Leave scope : {}'.format(funcName))




    def visit_VarDecl(self, node):
        type_name = node.type_node.value
        type_symbol = self.current_scope.lookup(type_name)

        # We have all the information we need to create a variable symbol.
        # Create the symbol and insert it into the symbol table.
        var_name = node.var_node.value
        var_symbol = VarSymbol(var_name, type_symbol)

        # Signal an error if the table already has a symbol
        # with the same name
        if self.current_scope.lookup(var_name, current_scope_only=True):
            self.error(
                error_code=ErrorCode.DUPLICATE_ID,
                token=node.var_node.token,
            )

        self.current_scope.insert(var_symbol)

    def visit_Assign(self, node):
        # right-hand side
        # self.visit(node.right)
        # # left-hand side
        # self.visit(node.left)
        varName=node.left.value
        currentScope=self.current_scope
        if currentScope.scopeType == TokenType.FUNCTION and varName== currentScope.ScopeName:
            currentScope.hasReturnStatement=True
        else:
            VarSymbol=self.current_scope.lookup(varName)
            if VarSymbol==None:
                self.error(error_code=ErrorCode.ID_NOT_FOUND, token=node.token)
        self.visit(node.right)

    def visit_Var(self, node):
        var_name = node.value
        var_symbol = self.current_scope.lookup(var_name)
        if var_symbol is None:
            self.error(error_code=ErrorCode.ID_NOT_FOUND, token=node.token)

    def visit_Num(self, node):
        pass

    def visit_UnaryOp(self, node):
        self.visit(node.right)

    def visit_ProcedureCall(self, node):
        for param_node in node.actual_params:
            self.visit(param_node)

    def visit_Call(self,node):
        for param_node in node.actual_params:
            self.visit(param_node)

    def visit_Condition(self,node):
        self.visit(node.condition)
        self.visit(node.then)
        if(node.myElse!=None):
            self.visit(node.myElse)

    def visit_Then(self,node):
        self.visit(node.child)

    def visit_MyElse(self,node):
        self.visit(node.child)

    def visit_While(self,node):
        self.visit(node.condition)

    def visit_MyDo(self,node):
        self.visit(node.child)
