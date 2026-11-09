#include <gtest/gtest.h>
#include "version_check.h"

TEST(VersionCheckTest, HandlesNullPointer) {
    EXPECT_TRUE(is_hash_invalid(nullptr));
}

TEST(VersionCheckTest, RejectsShortStrings) {
    EXPECT_TRUE(is_hash_invalid("abc"));
    EXPECT_TRUE(is_hash_invalid(""));
}

TEST(VersionCheckTest, AcceptsValidStrings) {
    EXPECT_FALSE(is_hash_invalid("abcd"));
    EXPECT_FALSE(is_hash_invalid("1234-5678"));
    EXPECT_FALSE(is_hash_invalid("a1b2c3d4"));
}