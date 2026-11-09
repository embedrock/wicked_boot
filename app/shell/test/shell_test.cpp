#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include <string>
#include <cstring>
#include <cstdlib>
#include "shell/shell.h"

// Тестовый буфер для перехвата вывода 
static std::string g_output_buffer;

// Мок для send_char
static int mock_send_char(char c) {
    g_output_buffer += c;
    return 0;
}

// Мок для handler команды
static int mock_handler_called = 0;
static int mock_argc_received = 0;
static char* mock_argv0_received = nullptr;

static int mock_command_handler(int argc, char *argv[]) {
    mock_handler_called++;
    mock_argc_received = argc;
    if (argc > 0 && argv[0] != nullptr) {
        mock_argv0_received = strdup(argv[0]);
    }
    return 0;
}

// Тестовый массив команд
static const sShellCommand g_test_commands[] = {
    {"test_cmd", mock_command_handler, "Test command"},
    {"help", shell_help_handler, "Show help"}
};

// Глобальные переменные для shell.c
extern "C" {
    const sShellCommand *const g_shell_commands = g_test_commands;
    const size_t g_num_shell_commands = sizeof(g_test_commands) / sizeof(g_test_commands[0]);
}

class ShellTest : public ::testing::Test {
protected:
    void SetUp() override {
        g_output_buffer.clear();
        mock_handler_called = 0;
        mock_argc_received = 0;
        if (mock_argv0_received) {
            free(mock_argv0_received);
            mock_argv0_received = nullptr;
        }
        
        sShellImpl impl = {mock_send_char};
        shell_boot(&impl);
        g_output_buffer.clear(); // Очищаем промпт после boot
    }
    
    void TearDown() override {
        if (mock_argv0_received) {
            free(mock_argv0_received);
            mock_argv0_received = nullptr;
        }
    }
    
    void sendString(const std::string& str) {
        for (char c : str) {
            shell_receive_char(c);
        }
    }
};

// ИСПРАВЛЕНО: используем \r вместо \n
TEST_F(ShellTest, UnknownCommandPrintsError) {
    sendString("invalid_cmd\r");
    
    EXPECT_THAT(g_output_buffer, testing::HasSubstr("Unknown command: invalid_cmd"));
    EXPECT_EQ(mock_handler_called, 0);
}

// ИСПРАВЛЕНО: используем \r вместо \n
TEST_F(ShellTest, ValidCommandCallsHandler) {
    sendString("test_cmd\r");
    
    EXPECT_EQ(mock_handler_called, 1);
    EXPECT_EQ(mock_argc_received, 1);
    EXPECT_STREQ(mock_argv0_received, "test_cmd");
}

// ИСПРАВЛЕНО: используем \r вместо \n
TEST_F(ShellTest, CommandWithArguments) {
    sendString("test_cmd arg1 arg2\r");
    
    EXPECT_EQ(mock_handler_called, 1);
    EXPECT_EQ(mock_argc_received, 3);
    EXPECT_STREQ(mock_argv0_received, "test_cmd");
}

// ИСПРАВЛЕНО: используем \r вместо \n
TEST_F(ShellTest, BackspaceRemovesCharacter) {
    sendString("abc\b\b\r");
    
    // После двух backspace в буфере остается только "a"
    EXPECT_THAT(g_output_buffer, testing::HasSubstr("Unknown command: a"));
}

// ИСПРАВЛЕНО: используем \r вместо \n
TEST_F(ShellTest, EmptyCommandDoesNothing) {
    sendString("\r");
    
    EXPECT_EQ(mock_handler_called, 0);
    EXPECT_THAT(g_output_buffer, testing::Not(testing::HasSubstr("Unknown command")));
}