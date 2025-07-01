/*
 *
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 *
 */

#include <proton/connection.hpp>
#include <proton/connection_options.hpp>
#include <proton/container.hpp>
#include <proton/messaging_handler.hpp>
#include <proton/reconnect_options.hpp>
#include <proton/transport.hpp>

#include <iostream>
#include <string>

struct failover_handler : public proton::messaging_handler {
    std::string primary_url_;
    std::vector<std::string> failover_urls_;

    void on_container_start(proton::container& cont) override {
        proton::connection_options opts {};
        proton::reconnect_options ropts {};

        ropts.failover_urls(failover_urls_);
        opts.reconnect(ropts);

        cont.connect(primary_url_, opts);
    }

    void on_connection_open(proton::connection& conn) override {
        std::cout << "Connected to " << conn.transport() << "\n";
    }
};

int main(int argc, char** argv) {
    failover_handler handler {};
    handler.primary_url_ = argv[1];
    handler.failover_urls_ = std::vector<std::string>(&argv[2], &argv[argc]);

    proton::container cont {handler};
    cont.run();
}
